from setuptools import setup, find_packages

setup(
    name="fastapi-ratelimiter",
    version="0.1.0",
    description="A FastAPI middleware for rate limiting using Redis.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Hossein Kalantari",
    author_email="hosseinkalantari.29@gmail.com",
    url="https://github.com/hosseink9/fastapi-ratelimiter",  # Update with your repo
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "starlette",
        "redis",
        "asyncio",
        "uvicorn",  # if you're running an ASGI server
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
