from jinja2 import Environment, FileSystemLoader
import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
from resume_manager import ResumeContent, ManualContentFilter, ResumeManager, ContentFilter, OpenAIContentFilter
import logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TODO: add path to env variables
TEMPLATE = os.getenv("TEMPLATE", "template.jinja")
DATA = os.getenv("DATA", "resume_content.yaml")
OUTPUT = os.getenv("OUTPUT", "output.tex")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTRUCTIONS = os.getenv("INSTRUCTIONS", "instructions.txt")
JOB_LISTING = os.getenv("JOB_LISTING", "example_listing.txt")


def get_content_filter():
    # content_filter = ManualContentFilter(filter_indices_path="./data/test_filter.yaml")
    # content_filter = None
    with open(Path("data") / Path(INSTRUCTIONS), 'r') as f:
        instructions = f.read()
    content_filter = OpenAIContentFilter(api_key=OPENAI_API_KEY, instructions=instructions)
    return content_filter

def get_job_listing():
    with open(Path("data") / Path(JOB_LISTING), 'r') as f:
        job_listing = f.read()
    return job_listing


def render_template():
    # load jinja environment/template
    env = Environment(
        loader=FileSystemLoader("./templates"),
        variable_start_string='((*',
        variable_end_string='*))',
        block_start_string='((%',
        block_end_string='%))',
        comment_start_string='((#',
        comment_end_string='#))',
        autoescape=False  # Don't autoescape for LaTeX
    )
    template = env.get_template(TEMPLATE)
    
    # load resume content
    data_path = Path("./data") / DATA
    with open(data_path, 'r') as f:
        data = yaml.safe_load(f)
    
    handler = ResumeManager(
        data, 
        job_listing=get_job_listing(),
        filter=get_content_filter(),
    ) 
    filtered_resume = handler.get_filtered_resume()
    rendered = template.render(resume=filtered_resume.model_dump())
    # Save rendered output to file
    output_path = Path("./output") / OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(rendered)

if __name__ == "__main__":
    render_template()
