import os

files = {
    "requirements.txt": "flask\nsqlmodel\npymysql\ncryptography",
    "app.py": """from flask import Flask, render_template, request, redirect, url_for, Response
from sqlmodel import SQLModel, create_engine, Session, select, Field, Relationship
from typing import List, Optional

app = Flask(__name__)
# SQLite para desenvolvimento local rápido, MySQL em produção
engine = create_engine("sqlite:///database.db")

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    items: List["ProjectItem"] = Relationship(back_populates="project")

class ProjectItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str 
    name: str
    requirements: str
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="items")

SQLModel.metadata.create_all(engine)

@app.route('/')
def index():
    with Session(engine) as session:
        projects = session.exec(select(Project)).all()
        return render_template('index.html', projects=projects)

@app.route('/project/new', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        with Session(engine) as session:
            project = Project(name=request.form['name'], description=request.form['description'])
            session.add(project)
            session.commit()
            return redirect(url_for('index'))
    return render_template('new_project.html')

@app.route('/project/<int:id>')
def view_project(id):
    with Session(engine) as session:
        project = session.get(Project, id)
        return render_template('project.html', project=project)

@app.route('/project/<int:id>/add_item', methods=['POST'])
def add_item(id):
    with Session(engine) as session:
        item = ProjectItem(
            type=request.form['type'],
            name=request.form['name'],
            requirements=request.form['requirements'],
            project_id=id
        )
        session.add(item)
        session.commit()
        return redirect(url_for('view_project', id=id))

@app.route('/project/<int:id>/export')
def export_md(id):
    with Session(engine) as session:
        project = session.get(Project, id)
        md = f"# Prompt de Criação: {project.name}\\n\\n"
        md += f"## Descrição Geral\\n{project.description}\\n\\n"
        for item in project.items:
            md += f"### {item.type.upper()}: {item.name}\\n**Requisitos:**\\n{item.requirements}\\n\\n"
        
        return Response(md, mimetype="text/markdown", 
                        headers={"Content-disposition": f"attachment; filename={project.name}.md"})

if __name__ == '__main__':
    app.run(debug=True)""",
    "templates/index.html": """<!DOCTYPE html>
<html>
<head><title>Architect - Projetos</title></head>
<body>
    <h1>Projetos de Software</h1>
    <a href="/project/new">+ Novo Projeto</a>
    <hr>
    <ul>
    {% for p in projects %}
        <li><a href="/project/{{p.id}}"><strong>{{p.name}}</strong></a> - {{p.description}}</li>
    {% endfor %}
    </ul>
</body>
</html>""",
    "templates/new_project.html": """<!DOCTYPE html>
<html>
<head><title>Novo Projeto</title></head>
<body>
    <h1>Criar Novo Projeto</h1>
    <form method="POST">
        <input type="text" name="name" placeholder="Nome do Projeto" required><br><br>
        <textarea name="description" placeholder="Descrição Geral"></textarea><br><br>
        <button type="submit">Salvar Projeto</button>
    </form>
</body>
</html>""",
    "templates/project.html": """<!DOCTYPE html>
<html>
<head><title>{{ project.name }}</title></head>
<body>
    <h1>{{ project.name }}</h1>
    <p>{{ project.description }}</p>
    <a href="/project/{{project.id}}/export" style="background: green; color: white; padding: 10px;">Gerar Prompt .MD</a>
    <hr>
    <h3>Adicionar Requisito (Web, App ou API)</h3>
    <form action="/project/{{project.id}}/add_item" method="POST">
        <select name="type">
            <option value="web">Web (Frontend/Dashboard)</option>
            <option value="api">Backend (API/Serviços)</option>
            <option value="mobile">Mobile (Android/iOS)</option>
        </select>
        <input type="text" name="name" placeholder="Ex: Tela de Login" required><br><br>
        <textarea name="requirements" placeholder="Descreva as funcionalidades aqui..."></textarea><br><br>
        <button type="submit">Adicionar ao Projeto</button>
    </form>
    <hr>
    <h3>Estrutura Atual</h3>
    {% for item in project.items %}
        <div>
            <strong>[{{ item.type.upper() }}] {{ item.name }}</strong>
            <p>{{ item.requirements }}</p>
        </div>
    {% endfor %}
    <br><a href="/">Voltar</a>
</body>
</html>""",
}


def setup():
    for path, content in files.items():
        (
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.dirname(path)
            else None
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Formulários e lógica de requisitos criados!")


if __name__ == "__main__":
    setup()
