from agent import run_agent

if __name__ == "__main__":
    digest = run_agent("Write today's AI news digest covering the last 24 hours.")
    print("\n" + digest)