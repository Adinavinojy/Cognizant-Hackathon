import html
import re
from html.parser import HTMLParser
from pathlib import Path
import chromadb
import pandas as pd


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.in_pre = False

    def handle_starttag(self, tag, attrs):
        if tag in ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr"]:
            self.result.append("\n\n")
        elif tag in ["br", "hr"]:
            self.result.append("\n")
        elif tag == "li":
            self.result.append("\n• ")
        elif tag == "pre":
            self.in_pre = True
            self.result.append("\n```\n")

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_pre = False
            self.result.append("\n```\n")

    def handle_data(self, data):
        self.result.append(data)

    def get_text(self) -> str:
        raw = "".join(self.result)
        decoded = html.unescape(raw)
        lines = [line.rstrip() for line in decoded.split("\n")]
        clean = "\n".join(lines)
        return re.sub(r"\n{3,}", "\n\n", clean).strip()


def clean_html(raw_html: str) -> str:
    if not isinstance(raw_html, str) or not raw_html.strip():
        return ""
    parser = HTMLTextExtractor()
    parser.feed(raw_html)
    return parser.get_text()


def classify_role_and_topic(tags_str: str) -> tuple[str, str]:
    tags = re.findall(r"<([^>]+)>", str(tags_str).lower())

    devops_tags = {"git", "git-branch", "version-control", "bash", "shell", "linux", "vim", "docker", "unix"}
    frontend_tags = {"javascript", "html", "css", "jquery", "reactjs", "typescript", "dom", "vue.js"}
    backend_tags = {"python", "java", "c#", ".net", "node.js", "sql", "sql-server", "c++", "c", "postgresql", "mysql", "api"}

    if any(t in devops_tags for t in tags):
        role = "DevOps Engineer"
    elif any(t in frontend_tags for t in tags):
        role = "Frontend Engineer"
    elif any(t in backend_tags for t in tags):
        role = "Backend Engineer"
    else:
        role = "Software Engineer"

    if any(t in {"git", "git-branch", "version-control"} for t in tags):
        topic = "Git & Version Control"
    elif any(t in {"linux", "bash", "shell", "vim"} for t in tags):
        topic = "Linux & Shell"
    elif any(t in {"javascript", "jquery", "typescript"} for t in tags):
        topic = "JavaScript / Web"
    elif any(t in {"html", "css"} for t in tags):
        topic = "HTML & CSS"
    elif "python" in tags:
        if any(t in {"dictionary", "list", "arrays", "string", "loops"} for t in tags):
            topic = "Python / Data Structures"
        else:
            topic = "Python Core"
    elif "java" in tags:
        topic = "Java Core"
    elif any(t in {"c#", ".net"} for t in tags):
        topic = "C# / .NET"
    elif any(t in {"c++", "c"} for t in tags):
        topic = "C / C++ Systems"
    elif any(t in {"sql", "sql-server", "database", "postgresql", "mysql"} for t in tags):
        topic = "Databases & SQL"
    elif tags:
        topic = tags[0].replace("-", " ").title()
    else:
        topic = "General Programming"

    return role, topic


def infer_difficulty(score: int) -> str:
    if score < 1800:
        return "Easy"
    elif score < 3000:
        return "Medium"
    return "Hard"


def run_ingestion():
    current_dir = Path(__file__).resolve().parent
    csv_path = current_dir / "QueryResults.csv"
    chroma_dir = current_dir.parent / "chroma_db"

    print(f"Reading dataset from: {csv_path}")
    df_raw = pd.read_csv(csv_path)

    documents = []
    ids = []
    metadatas = []

    for _, row in df_raw.iterrows():
        title = html.unescape(str(row.get("Title", "")).strip())
        q_body = clean_html(str(row.get("QuestionBody", "")))
        ans_body = clean_html(str(row.get("AnswerBody", "")))

        question_text = f"{title}\n\n{q_body}".strip() if q_body else title
        role, topic = classify_role_and_topic(str(row.get("Tags", "")))
        difficulty = infer_difficulty(int(row.get("Score", 0)))

        q_id = str(row.get("QuestionId"))
        ids.append(q_id)
        documents.append(question_text)
        metadatas.append({
            "role": role,
            "topic": topic,
            "difficulty": difficulty,
            "reference_answer": ans_body
        })

    print(f"Parsed {len(ids)} questions. Populating ChromaDB at {chroma_dir}...")
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name="question_bank",
        metadata={"hnsw:space": "cosine"}
    )

    batch_size = 250
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size]
        )
    print("Ingestion complete.")


if __name__ == "__main__":
    run_ingestion()