from flask import Flask, render_template, request, redirect, url_for, Response, flash
from sqlmodel import SQLModel, create_engine, Session, select, Field, Relationship
from typing import List, Optional
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "uma-chave-muito-segura"
engine = create_engine("sqlite:///database.db")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# --- Modelos ---
class User(SQLModel, UserMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    items: List["ProjectItem"] = Relationship(back_populates="project")


class ProjectItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    name: str
    requirements: str
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="items")


SQLModel.metadata.create_all(engine)


@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as session:
        return session.get(User, int(user_id))


# --- Rotas de Autenticação ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with Session(engine) as session:
            user = session.exec(
                select(User).where(User.username == request.form["username"])
            ).first()
            if user and check_password_hash(
                user.password_hash, request.form["password"]
            ):
                login_user(user)
                return redirect(url_for("index"))
            flash("Usuário ou senha inválidos")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        with Session(engine) as session:
            hashed_pw = generate_password_hash(request.form["password"])
            user = User(username=request.form["username"], password_hash=hashed_pw)
            session.add(user)
            session.commit()
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    with Session(engine) as session:
        projects = session.exec(
            select(Project).where(Project.owner_id == current_user.id)
        ).all()
        return render_template("index.html", projects=projects, user=current_user)


@app.route("/project/new", methods=["GET", "POST"])
@login_required
def new_project():
    if request.method == "POST":
        with Session(engine) as session:
            project = Project(
                name=request.form["name"],
                description=request.form["description"],
                owner_id=current_user.id,
            )
            session.add(project)
            session.commit()
            return redirect(url_for("index"))
    return render_template("new_project.html")


@app.route("/project/<int:id>")
def view_project(id):
    with Session(engine) as session:
        project = session.get(Project, id)
        return render_template("project.html", project=project)


@app.route("/project/<int:id>/add_item", methods=["POST"])
def add_item(id):
    with Session(engine) as session:
        item = ProjectItem(
            type=request.form["type"],
            name=request.form["name"],
            requirements=request.form["requirements"],
            project_id=id,
        )
        session.add(item)
        session.commit()
        return redirect(url_for("view_project", id=id))


@app.route("/project/<int:id>/export")
def export_md(id):
    with Session(engine) as session:
        project = session.get(Project, id)
        md = f"# Prompt de Criação: {project.name}\n\n"
        md += f"## Descrição Geral\n{project.description}\n\n"
        for item in project.items:
            md += f"### {item.type.upper()}: {item.name}\n**Requisitos:**\n{item.requirements}\n\n"

        return Response(
            md,
            mimetype="text/markdown",
            headers={"Content-disposition": f"attachment; filename={project.name}.md"},
        )


@app.route("/project/<int:project_id>/item/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(project_id, item_id):
    with Session(engine) as session:
        item = session.get(ProjectItem, item_id)
        if request.method == "POST":
            item.type = request.form["type"]
            item.name = request.form["name"]
            item.requirements = request.form["requirements"]
            session.add(item)
            session.commit()
            return redirect(url_for("view_project", id=project_id))
        return render_template("edit_item.html", item=item, project_id=project_id)


@app.route("/project/<int:project_id>/item/<int:item_id>/delete", methods=["POST"])
def delete_item(project_id, item_id):
    with Session(engine) as session:
        item = session.get(ProjectItem, item_id)
        session.delete(item)
        session.commit()
        return redirect(url_for("view_project", id=project_id))


if __name__ == "__main__":
    app.run(debug=True)
