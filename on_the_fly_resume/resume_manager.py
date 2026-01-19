from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List
import yaml
from copy import deepcopy
import logging
from openai import OpenAI
from openai.types.responses import Response
import time

logger = logging.getLogger(__name__)


class ResumeContent(BaseModel):
    """Resume content model."""
    experience: List['ExperienceItem']


class ExperienceItem(BaseModel):
    """Experience item model."""
    title: str
    company: str
    start_date: str
    end_date: str
    location: str
    responsibilities: List[str]


class ContentFilter(ABC):
    """Abstract base class for content filter.
    
    All content filters filter using a FilterIndices object that contains the indices
    in each resume section to keep. The difference between each type of content filter
    is how those indices are determined."""
    
    #TODO: validation logic to make sure filter matches content
    class FilterIndices(BaseModel):
        experience_filters: List[List[int]]
        # add projects, skills, etc.

    @abstractmethod
    def get_filter_keys(self, job_listing: str, content: ResumeContent) -> FilterIndices:
        """Return a dictionary containing list indices of resume items to keep."""
        pass

    def filter_resume_content(self, job_listing: str, content: ResumeContent) -> ResumeContent:
        """Receive a ResumeContent and return a filtered ResumeContent."""
        all_filters = self.get_filter_keys(job_listing, content)
        logger.debug(f"Filter keys: {all_filters}")
        
        filtered_content = deepcopy(content)
        for i, (filter, experience_item) in enumerate(zip(all_filters.experience_filters, content.experience)):
            logger.debug(f"Experience item {i}: {experience_item.title} at {experience_item.company}")
            logger.debug(f"Original responsibilities count: {len(experience_item.responsibilities)}")
            logger.debug(f"Filter indices: {filter}")
            filtered_content.experience[i].responsibilities = [experience_item.responsibilities[j] for j in filter]
            logger.debug(f"Filtered responsibilities count: {len(filtered_content.experience[i].responsibilities)}")
        return filtered_content
    

class ManualContentFilter(ContentFilter):
    """Content filter that uses manually specified indices."""

    def __init__(self, indices: ContentFilter.FilterIndices = None, filter_indices_path: str = None):
        if filter_indices_path:
            with open(filter_indices_path, 'r') as f:
                data = yaml.safe_load(f)
                self.indices = ContentFilter.FilterIndices(**data)
        elif indices:
            self.indices = indices
        else:
            raise ValueError("Either indices or filter_indices_path must be provided")

    def get_filter_keys(self, job_listing: str, content: ResumeContent) -> ContentFilter.FilterIndices:
        return self.indices
    

class OpenAIContentFilter(ContentFilter):
    """Content filter that uses an OpenAI model for content filtering."""

    def __init__(
            self, 
            api_key: str, 
            instructions: str,
            model: str = "gpt-5-mini"
        ):
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        self.instructions = instructions
        self.model = model
    
    def get_response(self, prompt: str) -> Response:
        # logger.debug(f"OpenAI model prompt: {prompt}")
        logger.info("Making OpenAI API call.")
        start_time = time.time()
        response = self.client.responses.create(
            model=self.model,
            instructions=self.instructions,
            input=prompt,
        )
        elapsed_time = time.time() - start_time
        logger.info(f"OpenAI API call took {elapsed_time:.2f} seconds")
        response = self.client.responses.create(
            model=self.model,
            instructions=self.instructions,
            input=prompt,
        )
        logger.debug(f"OpenAI model response: {response.output_text}")
        return response.output_text
        

    def get_filter_keys(self, job_listing: str, content: ResumeContent) -> ContentFilter.FilterIndices:
        candidate = f"Here is the candidate file: \n\n {yaml.dump(content.model_dump(), width=float('inf'), sort_keys=True)}"
        prompt = f"{job_listing} \n {candidate}"
        llm_response = yaml.safe_load(self.get_response(prompt))
        return ContentFilter.FilterIndices(experience_filters=llm_response["content"])


class ResumeManager:
    """Handler for a generated resume."""

    def __init__(
            self, 
            data: dict, 
            job_listing: str,
            filter: ContentFilter=None,
        ):
        self.resume_content = ResumeContent(**data)
        self.job_listing = job_listing
        self.filter = filter 

    def get_filtered_resume(self) -> ResumeContent:
        return self.filter.filter_resume_content(self.job_listing, self.resume_content) if self.filter else self.resume_content

