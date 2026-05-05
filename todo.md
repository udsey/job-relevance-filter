Handling Rate Limits and Blocks

LinkedIn will start returning 429 errors if you scrape too fast. A few practical tips:

    Add delays: 2-3 seconds between requests minimum
    Rotate User-Agents: Use a pool of realistic browser UA strings
    Use proxy rotation: Essential for any serious volume
    Implement exponential backoff: Double your wait time after each 429 error

User-Agent Rotation

import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

def get_random_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

