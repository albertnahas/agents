from pydantic import BaseModel, Field
from agents import Agent, ModelSettings

NUM_IDEAS_TO_GENERATE = 10

INSTRUCTIONS = (
    "You are a senior ideas generator tasked with generating " + str(NUM_IDEAS_TO_GENERATE) + " relevant novel feasible and valuable ideas. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "generate the ideas and return that as your final output.\n"
    "The final output should be a detailed list of ideas, each with a description of the idea, its potential impact, and any relevant considerations.\n"
)


class IdeaItem(BaseModel):
    title: str = Field(description="The title of the idea.")
    description: str = Field(description="A description of the idea.")

class IdeaList(BaseModel):
    ideas: list[IdeaItem] = Field(description="A list of generated ideas.")

generator_agent = Agent(
    name="GeneratorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-5-mini",
    output_type=IdeaList,
)