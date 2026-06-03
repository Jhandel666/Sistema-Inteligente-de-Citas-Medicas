from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password_plano = "Admin1234"
password_hash = pwd_context.hash(password_plano)

print(password_hash)