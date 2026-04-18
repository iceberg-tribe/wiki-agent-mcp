from setuptools import setup, find_packages

setup(
    name="wiki-agent-mcp",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp>=0.1.0",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "wiki-agent-mcp=wiki_agent_mcp.main:main",
        ],
    },
    python_requires=">=3.12",
)