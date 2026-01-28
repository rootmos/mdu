import datetime
import json
import subprocess
import os

script_dir = os.path.dirname(os.path.realpath(__file__))
root = os.getenv("ROOT", script_dir)
tools = os.getenv("TOOLS", os.path.realpath(os.path.join(root, "tools")))

def render_terraform_outputs():
    target = os.path.join(root, "src/schema/terraform.py")
    if os.path.exists(target):
        return

    raw = subprocess.check_output(["terraform", "output", "-json"], cwd=root)
    j = json.loads(raw)

    print(f"fetching terraform outputs: {target}")
    with open(target, "x") as f:
        f.write(f"# terraform outputs: {datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')}\n")

        for k, v in j.items():
            if v["sensitive"]:
                continue
            match v["type"]:
                case "string":
                    # TODO escape?
                    f.write(f'{k} = "{v["value"]}"\n')
                case t:
                    raise RuntimeError(f"unsupported type: {t}")

def render_build_info():
    build_info_script = os.path.join(tools, "build-info")
    target = os.path.join(root, "src/schema/build_info.py")
    subprocess.check_call([build_info_script, "-Po", target])

def build() -> None:
    render_terraform_outputs()
    render_build_info()

if __name__ == "__main__":
    build()
