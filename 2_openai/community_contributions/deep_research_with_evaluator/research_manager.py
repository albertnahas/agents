from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from evaluator_agent import IdeaEvaluation, evaluator_agent, EvaluationResult
from generator_agent import generator_agent, IdeaItem
import asyncio

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, generating ideas..."
            max_attempts = 3
            attempt = 0
            evaluation = None
            
            winners = []
            while attempt < max_attempts and len(winners) < 5:
                # generate ideas based on the search results
                ideas = await self.generate_ideas(query, search_results)
                yield f"Ideas generated (attempt {attempt + 1}/{max_attempts}), evaluating..."
                evaluation = await self.evaluate_ideas(query, ideas)
                yield f"Ideas evaluated (attempt {attempt + 1}/{max_attempts})..."
                # Filter out ideas with failure reasons and add to winners
                valid_ideas = [idea for idea in evaluation.ideas if not idea.failure_reason]
                winners.extend(valid_ideas)
                
                attempt += 1
                if len(winners) < 5 and attempt < max_attempts:
                    yield f"Found {len(winners)} valid ideas so far, trying again..."

            if len(winners) < 5:
                raise ValueError(f"Only found {len(winners)} valid ideas after maximum attempts")
                
            evaluation = EvaluationResult(ideas=winners)
            
            if not evaluation or not evaluation.ideas:
                raise ValueError("Failed to generate valid ideas after maximum attempts")
            report = await self.write_report(query, evaluation.ideas)
            yield report.markdown_report
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def generate_ideas(self, query: str, search_results: list[str]) -> list[IdeaItem]:
        """ Generate ideas for the query """
        print("Generating ideas...")
        input = f"Query: {query}\nIdeas evaluation: {search_results}"
        result = await Runner.run(
            generator_agent,
            input,
        )
        print("Finished generating ideas")
        return result.final_output_as(list[IdeaItem])

    async def write_report(self, query: str, ideas: list[IdeaEvaluation]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        ideas_list = [{"title": idea.title, "description": idea.description} for idea in ideas]
        input = f"Original query: {query}\nSummarized search results: {ideas_list}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def evaluate_ideas(self, query: str, ideas: list[IdeaItem]) -> EvaluationResult:
        """ Evaluate the generated ideas """
        print("Evaluating ideas...")
        input = f"Query: {query}\nIdeas: {ideas}"
        result = await Runner.run(
            evaluator_agent,
            input,
        )
        print("Finished evaluating ideas")
        return result.final_output_as(EvaluationResult)
