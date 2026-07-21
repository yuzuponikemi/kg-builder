"""LLM-based relevance filtering for research papers."""

from dataclasses import dataclass
from typing import Any

from kg_builder.extractor.llm_client import get_llm_client
from kg_builder.search.arxiv_search import ArxivPaper


@dataclass
class RelevanceScore:
    """Relevance score for a paper."""

    paper: ArxivPaper
    score: float  # 0.0 to 1.0
    reasoning: str
    is_relevant: bool

    def __str__(self) -> str:
        """String representation."""
        status = "✓ RELEVANT" if self.is_relevant else "✗ NOT RELEVANT"
        return (
            f"{status} (score: {self.score:.2f})\n"
            f"  {self.paper.arxiv_id}: {self.paper.title}\n"
            f"  Reasoning: {self.reasoning}"
        )


class LLMRelevanceFilter:
    """Filter papers using LLM-based relevance assessment."""

    RELEVANCE_PROMPT = """You are a research paper relevance assessor. Your task is to determine how relevant a research paper is to a given query or research interest.

Query/Research Interest:
{query}

Paper to Assess:
Title: {title}
Authors: {authors}
Abstract: {abstract}
Categories: {categories}
Published: {published}

Please assess the relevance of this paper to the query. Consider:
1. Does the paper directly address the query topic?
2. Are the methods, results, or findings relevant to the query?
3. Would this paper be valuable for someone researching this topic?
4. Is the paper recent and relevant to current research?

Provide your assessment as a JSON object with:
- score: A relevance score from 0.0 (completely irrelevant) to 1.0 (highly relevant)
- reasoning: A brief explanation (1-2 sentences) of why you gave this score
- is_relevant: Boolean - true if score >= {threshold}, false otherwise

Respond with JSON only:
{{
  "score": 0.85,
  "reasoning": "This paper directly addresses X and provides Y which is central to the query.",
  "is_relevant": true
}}"""

    def __init__(self, llm_client: Any | None = None, threshold: float = 0.6):
        """Initialize relevance filter.

        Args:
            llm_client: LLM client instance. If None, creates a new one.
            threshold: Relevance threshold (0.0-1.0). Papers scoring above
                      this are considered relevant.
        """
        self.llm = llm_client or get_llm_client()
        self.threshold = threshold

    def assess_relevance(self, paper: ArxivPaper, query: str) -> RelevanceScore:
        """Assess relevance of a paper to a query.

        Args:
            paper: ArxivPaper to assess
            query: User's research query or interest

        Returns:
            RelevanceScore with assessment
        """
        # Format authors
        authors_str = ", ".join(paper.authors[:5])
        if len(paper.authors) > 5:
            authors_str += f" et al. ({len(paper.authors)} total)"

        # Create prompt
        prompt = self.RELEVANCE_PROMPT.format(
            query=query,
            title=paper.title,
            authors=authors_str,
            abstract=paper.abstract[:1000],  # Truncate long abstracts
            categories=", ".join(paper.categories),
            published=paper.published.strftime("%Y-%m-%d"),
            threshold=self.threshold,
        )

        try:
            # Get LLM assessment
            response = self.llm.generate(
                prompt=prompt, temperature=0.0, response_format="json", max_tokens=500
            )

            # Parse response
            data = self.llm.extract_json(response)

            score = float(data.get("score", 0.0))
            reasoning = data.get("reasoning", "No reasoning provided")
            is_relevant = bool(data.get("is_relevant", score >= self.threshold))

            return RelevanceScore(
                paper=paper, score=score, reasoning=reasoning, is_relevant=is_relevant
            )

        except Exception as e:
            print(f"Warning: Failed to assess relevance for {paper.arxiv_id}: {e}")
            # Return neutral score on error
            return RelevanceScore(
                paper=paper,
                score=0.5,
                reasoning=f"Error during assessment: {e}",
                is_relevant=False,
            )

    def filter_papers(
        self, papers: list[ArxivPaper], query: str, verbose: bool = True
    ) -> list[RelevanceScore]:
        """Filter papers by relevance to query.

        Args:
            papers: List of papers to assess
            query: Research query
            verbose: Print progress

        Returns:
            List of RelevanceScore objects, sorted by score (highest first)
        """
        if verbose:
            print(f"\nAssessing relevance of {len(papers)} papers to query...")
            print(f"Query: {query}\n")

        scores = []
        for i, paper in enumerate(papers, 1):
            if verbose:
                print(f"[{i}/{len(papers)}] Assessing: {paper.arxiv_id}")

            score = self.assess_relevance(paper, query)
            scores.append(score)

            if verbose:
                status = "✓" if score.is_relevant else "✗"
                print(f"  {status} Score: {score.score:.2f} - {score.reasoning}\n")

        # Sort by score (highest first)
        scores.sort(key=lambda x: x.score, reverse=True)

        return scores

    def get_relevant_papers(
        self, papers: list[ArxivPaper], query: str, verbose: bool = True
    ) -> list[ArxivPaper]:
        """Get only relevant papers.

        Args:
            papers: Papers to filter
            query: Research query
            verbose: Print progress

        Returns:
            List of relevant papers (score >= threshold)
        """
        scores = self.filter_papers(papers, query, verbose=verbose)
        return [score.paper for score in scores if score.is_relevant]

    def batch_assess(
        self,
        papers: list[ArxivPaper],
        query: str,
        top_n: int | None = None,
        min_score: float | None = None,
    ) -> list[RelevanceScore]:
        """Assess papers and return top results.

        Args:
            papers: Papers to assess
            query: Research query
            top_n: Return only top N papers by score
            min_score: Return only papers with score >= this

        Returns:
            List of RelevanceScore objects
        """
        scores = self.filter_papers(papers, query, verbose=False)

        # Apply filters
        if min_score is not None:
            scores = [s for s in scores if s.score >= min_score]

        if top_n is not None:
            scores = scores[:top_n]

        return scores
