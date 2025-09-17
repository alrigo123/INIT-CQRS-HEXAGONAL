# # tests/users/infrastructure/persistence/test_sqlalchemy_user_repository.py
# """
# Pruebas de integración para SQLAlchemyUserRepository.
# Estas pruebas verifican la interacción real con una base de datos.
# Para evitar afectar la BD principal, se puede usar una BD de prueba.
# En este ejemplo, se usará la misma configuración pero con una BD diferente o en memoria (si es posible).
# Para simplificar, usaremos una BD PostgreSQL efímera o una configuración especial.
# NOTA: Esta prueba requiere que la BD de prueba esté accesible.
# """

# import pytest
# import uuid
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import IntegrityError # Para probar errores de unicidad

#  # Importamos las clases que vamos a probar
# from app.users.infrastructure.persistence.database import Base # Asegúrate de importar Base correctamente
# from app.users.infrastructure.persistence.user_model import UserModel
# from app.users.infrastructure.persistence.repositories import SQLAlchemyUserRepository
 
#  # Importamos el dominio para crear entidades y probar la conversión
# from app.users.domain.models import User

# # --- Configuración específica para pruebas ---
# # Usar una BD de prueba separada. En este caso, usamos la misma configuración
# # pero podrías apuntar a una BD diferente o usar SQLite en memoria (sqlite:///:memory:)
# # Para este ejemplo, seguiremos usando PostgreSQL pero con una base de datos de prueba.
# # Asegúrate de que esta BD exista o que el usuario tenga permisos para crearla.
# # NOTA: Es buena práctica usar variables de entorno para la BD de pruebas.
# import os
# # Puedes definir TEST_DATABASE_URL en tu environment o en un .env de pruebas
# # Ejemplo: TEST_DATABASE_URL=postgresql://myapp_user:myapp_password@localhost:5432/test_myapp_db
# # Si no está definida, usamos la misma (NO RECOMENDADO para pruebas que modifican datos)
# TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://myapp_user:myapp_password@localhost:5432/test_myapp_db")


# @pytest.fixture(scope="function") # Se ejecuta una vez por función de prueba
# def test_db_session():
#     """
#     Fixture de pytest para crear una sesión de BD de prueba.
#     Crea las tablas antes de cada prueba y las elimina después.
#     """
#     # 1. Crear el engine para la BD de prueba
#     engine = create_engine(TEST_DATABASE_URL, echo=False) # echo=False para pruebas
    
#     # 2. Crear todas las tablas definidas en los modelos
#     # Esto asegura que las tablas estén limpias para cada prueba
#     Base.metadata.create_all(bind=engine)
    
#     # 3. Crear la fábrica de sesiones
#     TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
#     # 4. Crear una sesión para la prueba
#     session = TestingSessionLocal()
    
#     try:
#         yield session # Entregar la sesión a la prueba
#     finally:
#         # 5. Limpiar después de la prueba
#         session.close()
#         # Eliminar todas las tablas para dejar la BD limpia
#         # NOTA: Esto es lento. En entornos de CI, a veces se usa una BD efímera.
#         Base.metadata.drop_all(bind=engine)


# class TestSQLAlchemyUserRepository:
#     """Grupo de pruebas para SQLAlchemyUserRepository."""

#     def test_save_user_success(self, test_db_session):
#         """Prueba que se pueda guardar un usuario correctamente."""
#         # 1. Arrange
#         repository = SQLAlchemyUserRepository(test_db_session)
#         user_id = str(uuid.uuid4())
#         domain_user = User(
#             user_id=user_id,
#             name="Usuario de Prueba",
#             email="test@example.com",
#             hashed_password="contraseña_hasheada_segura"
#         )

#         # 2. Act
#         repository.save(domain_user)

#         # 3. Assert
#         # Verificar que el usuario fue guardado consultando directamente el modelo de SQLAlchemy
#         db_user_model = test_db_session.query(UserModel).filter(UserModel.id == user_id).first()
#         assert db_user_model is not None
#         assert db_user_model.name == domain_user.name
#         assert db_user_model.email == domain_user.email
#         assert db_user_model.hashed_password == domain_user.hashed_password

#     def test_get_user_by_id_success(self, test_db_session):
#         """Prueba que se pueda obtener un usuario por su ID correctamente."""
#         # 1. Arrange
#         repository = SQLAlchemyUserRepository(test_db_session)
#         user_id = str(uuid.uuid4())
#         # Crear un UserModel directamente y guardarlo en la BD para la prueba
#         db_user_model = UserModel(
#             id=user_id,
#             name="Usuario de Prueba",
#             email="test@example.com",
#             hashed_password="contraseña_hasheada_segura"
#         )
#         test_db_session.add(db_user_model)
#         test_db_session.commit()

#         # 2. Act
#         retrieved_domain_user = repository.get_by_id(user_id)

#         # 3. Assert
#         assert retrieved_domain_user is not None
#         assert isinstance(retrieved_domain_user, User) # Verifica el tipo
#         assert retrieved_domain_user.id == user_id
#         assert retrieved_domain_user.name == db_user_model.name
#         assert retrieved_domain_user.email == db_user_model.email
#         assert retrieved_domain_user.hashed_password == db_user_model.hashed_password

#     def test_get_user_by_id_not_found(self, test_db_session):
#         """Prueba que get_by_id devuelva None si el usuario no existe."""
#         # 1. Arrange
#         repository = SQLAlchemyUserRepository(test_db_session)
#         non_existent_id = str(uuid.uuid4())

#         # 2. Act
#         retrieved_domain_user = repository.get_by_id(non_existent_id)

#         # 3. Assert
#         assert retrieved_domain_user is None

#     def test_save_user_duplicate_email_raises_integrity_error(self, test_db_session):
#         """Prueba que guardar un usuario con email duplicado falle."""
#         # 1. Arrange
#         repository = SQLAlchemyUserRepository(test_db_session)
#         user_id_1 = str(uuid.uuid4())
#         user_id_2 = str(uuid.uuid4())
#         email = "duplicate@example.com"
        
#         domain_user_1 = User(
#             user_id=user_id_1,
#             name="Usuario 1",
#             email=email,
#             hashed_password="contraseña_hasheada_segura_1"
#         )
#         domain_user_2 = User(
#             user_id=user_id_2,
#             name="Usuario 2",
#             email=email, # Mismo email
#             hashed_password="contraseña_hasheada_segura_2"
#         )

#         # 2. Act & Assert
#         # Guardar el primer usuario debe funcionar
#         repository.save(domain_user_1)
        
#         # Guardar el segundo usuario con el mismo email debe fallar
#         with pytest.raises(RuntimeError) as excinfo:
#             repository.save(domain_user_2)
        
#         # Verificar que el mensaje de error sea descriptivo
#         # NOTA: El mensaje exacto puede variar, pero debería indicar un problema de integridad
#         assert "Error al guardar el usuario en la base de datos" in str(excinfo.value)
#         # O verificar la causa original si se relanza con `from e`
#         # assert "duplicate key value violates unique constraint" in str(excinfo.value.__cause__)
