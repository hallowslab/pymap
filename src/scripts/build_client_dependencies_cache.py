import json
import os


def run():
    content = ""
    package_file = os.path.join(os.path.abspath(os.curdir), "client/package.json")
    if not os.path.isfile("client/package.json"):
        raise FileNotFoundError(package_file)
    with open(package_file, "r") as fh:
        content = json.loads(fh.read())
        content = {
            "dependencies": content["dependencies"],
            "devDependencies": content["devDependencies"],
        }
    with open("client/package-dependencies.json", "w") as fh:
        json.dump(content, fh)
    exit(0)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        raise e
