from setuptools import setup, find_packages

setup(
    name="python-seo-spider",
    version="1.0.0",
    description="Comprehensive SEO crawling and analysis tool - Python alternative to Screaming Frog",
    author="SEO Spider",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.9.0",
        "httpx>=0.27.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.1.0",
        "playwright>=1.40.0",
        "tldextract>=5.1.0",
        "dnspython>=2.6.0",
        "fake-useragent>=1.4.0",
        "pandas>=2.1.0",
        "openpyxl>=3.1.0",
        "pyyaml>=6.0.0",
        "click>=8.1.0",
        "rich>=13.7.0",
        "tqdm>=4.66.0",
    ],
    entry_points={
        "console_scripts": [
            "seo-spider=main:main",
        ],
    },
)
