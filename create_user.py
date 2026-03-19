from app import engine, User
from sqlmodel import Session, select
from werkzeug.security import generate_password_hash
import getpass


def create_admin():
    username = input("Digite o nome de usuário: ")
    password = getpass.getpass("Digite a senha: ")

    with Session(engine) as session:
        # Forma correta usando session.exec() e select()
        statement = select(User).where(User.username == username)
        existing_user = session.exec(statement).first()

        if existing_user:
            print(f"Erro: Usuário '{username}' já existe.")
            return

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)

        session.add(new_user)
        session.commit()
        print(f"Usuário '{username}' criado com sucesso!")


if __name__ == "__main__":
    create_admin()
