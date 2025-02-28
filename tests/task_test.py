"""Test Agent creation and execution basic functionality."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel
from pydantic_core import ValidationError

from crewai import Agent, Crew, Task


def test_task_tool_reflect_agent_tools():
    from langchain.tools import tool

    @tool
    def fake_tool() -> None:
        "Fake tool"

    researcher = Agent(
        role="Researcher",
        goal="Make the best research and analysis on content about AI and AI agents",
        backstory="You're an expert researcher, specialized in technology, software engineering, AI and startups. You work as a freelancer and is now working on doing research and analysis for a new customer.",
        tools=[fake_tool],
        allow_delegation=False,
    )

    task = Task(
        description="Give me a list of 5 interesting ideas to explore for na article, what makes them unique and interesting.",
        agent=researcher,
    )

    assert task.tools == [fake_tool]


def test_task_tool_takes_precedence_over_agent_tools():
    from langchain.tools import tool

    @tool
    def fake_tool() -> None:
        "Fake tool"

    @tool
    def fake_task_tool() -> None:
        "Fake tool"

    researcher = Agent(
        role="Researcher",
        goal="Make the best research and analysis on content about AI and AI agents",
        backstory="You're an expert researcher, specialized in technology, software engineering, AI and startups. You work as a freelancer and is now working on doing research and analysis for a new customer.",
        tools=[fake_tool],
        allow_delegation=False,
    )

    task = Task(
        description="Give me a list of 5 interesting ideas to explore for an article, what makes them unique and interesting.",
        agent=researcher,
        tools=[fake_task_tool],
    )

    assert task.tools == [fake_task_tool]


def test_task_prompt_includes_expected_output():
    researcher = Agent(
        role="Researcher",
        goal="Make the best research and analysis on content about AI and AI agents",
        backstory="You're an expert researcher, specialized in technology, software engineering, AI and startups. You work as a freelancer and is now working on doing research and analysis for a new customer.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me a list of 5 interesting ideas to explore for na article, what makes them unique and interesting.",
        expected_output="Bullet point list of 5 interesting ideas.",
        agent=researcher,
    )

    with patch.object(Agent, "execute_task") as execute:
        execute.return_value = "ok"
        task.execute()
        execute.assert_called_once_with(task=task, context=None, tools=[])


def test_task_callback():
    researcher = Agent(
        role="Researcher",
        goal="Make the best research and analysis on content about AI and AI agents",
        backstory="You're an expert researcher, specialized in technology, software engineering, AI and startups. You work as a freelancer and is now working on doing research and analysis for a new customer.",
        allow_delegation=False,
    )

    task_completed = MagicMock(return_value="done")

    task = Task(
        description="Give me a list of 5 interesting ideas to explore for na article, what makes them unique and interesting.",
        expected_output="Bullet point list of 5 interesting ideas.",
        agent=researcher,
        callback=task_completed,
    )

    with patch.object(Agent, "execute_task") as execute:
        execute.return_value = "ok"
        task.execute()
        task_completed.assert_called_once_with(task.output)


def test_execute_with_agent():
    researcher = Agent(
        role="Researcher",
        goal="Make the best research and analysis on content about AI and AI agents",
        backstory="You're an expert researcher, specialized in technology, software engineering, AI and startups. You work as a freelancer and is now working on doing research and analysis for a new customer.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me a list of 5 interesting ideas to explore for na article, what makes them unique and interesting.",
        expected_output="Bullet point list of 5 interesting ideas.",
    )

    with patch.object(Agent, "execute_task", return_value="ok") as execute:
        task.execute(agent=researcher)
        execute.assert_called_once_with(task=task, context=None, tools=[])


def test_async_execution():
    researcher = Agent(
        role="Researcher",
        goal="Make the best research and analysis on content about AI and AI agents",
        backstory="You're an expert researcher, specialized in technology, software engineering, AI and startups. You work as a freelancer and is now working on doing research and analysis for a new customer.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me a list of 5 interesting ideas to explore for na article, what makes them unique and interesting.",
        expected_output="Bullet point list of 5 interesting ideas.",
        async_execution=True,
        agent=researcher,
    )

    with patch.object(Agent, "execute_task", return_value="ok") as execute:
        task.execute(agent=researcher)
        execute.assert_called_once_with(task=task, context=None, tools=[])


def test_multiple_output_type_error():
    class Output(BaseModel):
        field: str

    with pytest.raises(ValidationError):
        Task(
            description="Give me a list of 5 interesting ideas to explore for na article, what makes them unique and interesting.",
            expected_output="Bullet point list of 5 interesting ideas.",
            output_json=Output,
            output_pydantic=Output,
        )


@pytest.mark.vcr(filter_headers=["authorization"])
def test_output_pydantic():
    class ScoreOutput(BaseModel):
        score: int

    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_pydantic=ScoreOutput,
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task])
    result = crew.kickoff()
    assert isinstance(result, ScoreOutput)


@pytest.mark.vcr(filter_headers=["authorization"])
def test_output_json():
    class ScoreOutput(BaseModel):
        score: int

    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_json=ScoreOutput,
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task])
    result = crew.kickoff()
    assert '{\n  "score": 4\n}' == result


@pytest.mark.vcr(filter_headers=["authorization"])
def test_output_pydantic_to_another_task():
    class ScoreOutput(BaseModel):
        score: int

    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task1 = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_pydantic=ScoreOutput,
        agent=scorer,
    )

    task2 = Task(
        description="Given the score the title 'The impact of AI in the future of work' got, give me an integer score between 1-5 for the following title: 'Return of the Jedi'",
        expected_output="The score of the title.",
        output_pydantic=ScoreOutput,
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task1, task2])
    result = crew.kickoff()
    assert 4 == result.score


@pytest.mark.vcr(filter_headers=["authorization"])
def test_output_json_to_another_task():
    class ScoreOutput(BaseModel):
        score: int

    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task1 = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_json=ScoreOutput,
        agent=scorer,
    )

    task2 = Task(
        description="Given the score the title 'The impact of AI in the future of work' got, give me an integer score between 1-5 for the following title: 'Return of the Jedi'",
        expected_output="The score of the title.",
        output_json=ScoreOutput,
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task1, task2])
    result = crew.kickoff()
    assert '{\n  "score": 5\n}' == result


@pytest.mark.vcr(filter_headers=["authorization"])
def test_save_task_output():
    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_file="score.json",
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task])

    with patch.object(Task, "_save_file") as save_file:
        save_file.return_value = None
        crew.kickoff()
        save_file.assert_called_once()


@pytest.mark.vcr(filter_headers=["authorization"])
def test_save_task_json_output():
    class ScoreOutput(BaseModel):
        score: int

    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_file="score.json",
        output_json=ScoreOutput,
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task])

    with patch.object(Task, "_save_file") as save_file:
        save_file.return_value = None
        crew.kickoff()
        save_file.assert_called_once_with('{\n  "score": 4\n}')


@pytest.mark.vcr(filter_headers=["authorization"])
def test_save_task_pydantic_output():
    class ScoreOutput(BaseModel):
        score: int

    scorer = Agent(
        role="Scorer",
        goal="Score the title",
        backstory="You're an expert scorer, specialized in scoring titles.",
        allow_delegation=False,
    )

    task = Task(
        description="Give me an integer score between 1-5 for the following title: 'The impact of AI in the future of work'",
        expected_output="The score of the title.",
        output_file="score.json",
        output_pydantic=ScoreOutput,
        agent=scorer,
    )

    crew = Crew(agents=[scorer], tasks=[task])

    with patch.object(Task, "_save_file") as save_file:
        save_file.return_value = None
        crew.kickoff()
        save_file.assert_called_once_with('{"score":4}')
