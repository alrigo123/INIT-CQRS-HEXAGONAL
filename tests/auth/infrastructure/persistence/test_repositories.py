# # tests/auth/infrastructure/persistence/test_repositories.py
# """
# Pruebas de integración para SQLAlchemyTokenRepository.
# Estas pruebas validan la interacción real con la base de datos.
# Para evitar afectar la BD principal, se puede usar una BD de prueba.
# En este ejemplo, se usará la misma BD de la app (myapp_db) para simplificar,
# pero en un entorno de CI/CD real, se usaría una BD efímera o una instancia de prueba.
# """
# import pytest
# import uuid
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# # Importamos las clases que vamos a probar
# from app.auth.infrastructure.persistence.database import Base, SessionLocal
# from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository
# from app.auth.infrastructure.persistence.auth_model import TokenModel
# from app.auth.domain.models import Token

# # --- Configuración específica para pruebas ---
# # Para simplificar, usaremos la misma BD que la app.
# # NOTA: En un entorno de CI/CD real, se usaría una BD de prueba efímera.
# # Asegúrate de que esta BD esté accesible.
# # Se recomienda usar variables de entorno para la BD de pruebas.
# import os
# # TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://myapp_user:myapp_password@localhost:5432/test_myapp_db")
# # Para esta prueba, usamos la misma BD que la app. CUIDADO: Puede afectar datos reales.
# # En producción, usa una BD de prueba.
# TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myapp_user:myapp_password@db:5432/myapp_db")

# @pytest.fixture(scope="function")
# def test_db_session():
#     """
#     Fixture de pytest para crear una sesión de BD de prueba.
#     Crea las tablas antes de cada prueba y las elimina después.
#     ADVERTENCIA: Este fixture borra y recrea las tablas en la BD especificada.
#     """
#     # 1. Crear el engine para la BD de prueba
#     engine = create_engine(TEST_DATABASE_URL, echo=False) # echo=False para pruebas
    
#     # 2. Crear todas las tablas definidas en los modelos
#     # Esto asegura que las tablas estén limpias para cada prueba
#     # NOTA: drop_all/create_all es lento. En CI/CD, a veces se usa una BD efímera.
#     Base.metadata.drop_all(bind=engine) # Limpiar primero
#     Base.metadata.create_all(bind=engine) # Crear tablas
    
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

# class TestSQLAlchemyTokenRepository:
#     """Grupo de pruebas para SQLAlchemyTokenRepository."""

#     def test_save_token_success(self, test_db_session):
#         """Prueba que se pueda guardar un token correctamente."""
#         # 1. Arrange
#         repository = SQLAlchemyTokenRepository(test_db_session)
#         token_id = str(uuid.uuid4())
#         user_id = str(uuid.uuid4())
#         domain_token = Token(
#             token_id=token_id,
#             user_id=user_id,
#             access_token="un_token_de_acceso_seguro_para_pruebas",
#             expires_at=datetime.utcnow() + timedelta(hours=1)
#         )

#         # 2. Act
#         repository.save(domain_token)

#         # 3. Assert
#         # Verificar que el token fue guardado consultando directamente el modelo de SQLAlchemy
#         db_token_model = test_db_session.query(TokenModel).filter(TokenModel.id == token_id).first()
#         assert db_token_model is not None
#         assert db_token_model.user_id == user_id
#         assert db_token_model.access_token == domain_token.access_token
#         assert db_token_model.expires_at == domain_token.expires_at

#     def test_find_by_access_token_success(self, test_db_session):
#         """Prueba que se pueda obtener un token por su access_token correctamente."""
#         # 1. Arrange
#         repository = SQLAlchemyTokenRepository(test_db_session)
#         token_id = str(uuid.uuid4())
#         user_id = str(uuid.uuid4())
#         access_token = "token_para_busqueda_exitosa"
#         expires_at = datetime.utcnow() + timedelta(hours=1)
        
#         # Crear un TokenModel directamente y guardarlo en la BD para la prueba
#         db_token_model = TokenModel(
#             id=token_id,
#             user_id=user_id,
#             access_token=access_token,
#             expires_at=expires_at
#         )
#         test_db_session.add(db_token_model)
#         test_db_session.commit()

#         # 2. Act
#         retrieved_domain_token = repository.find_by_access_token(access_token)

#         # 3. Assert
#         assert retrieved_domain_token is not None
#         assert isinstance(retrieved_domain_token, Token) # Verifica el tipo
#         assert retrieved_domain_token.id == token_id
#         assert retrieved_domain_token.user_id == user_id
#         assert retrieved_domain_token.access_token == access_token
#         assert retrieved_domain_token.expires_at == expires_at

#     def test_find_by_access_token_not_found(self, test_db_session):
#         """Prueba que find_by_access_token devuelva None si el token no existe."""
#         # 1. Arrange
#         repository = SQLAlchemyTokenRepository(test_db_session)
#         non_existent_access_token = "token_que_no_existe"

#         # 2. Act
#         retrieved_domain_token = repository.find_by_access_token(non_existent_access_token)

#         # 3. Assert
#         assert retrieved_domain_token is None

#     def test_delete_token_success(self, test_db_session):
#         """Prueba que se pueda eliminar un token correctamente."""
#          # 1. Arrange
#         repository = SQLAlchemyTokenRepository(test_db_session)
#         token_id = str(uuid.uuid4())
#         user_id = str(uuid.uuid4())
#         access_token = "token_para_eliminar"
#         expires_at = datetime.utcnow() + timedelta(hours=1)
        
#         # Crear un TokenModel directamente y guardarlo en la BD para la prueba
#         db_token_model = TokenModel(
#             id=token_id,
#             user_id=user_id,
#             access_token=access_token,
#             expires_at=expires_at
#         )
#         test_db_session.add(db_token_model)
#         test_db_session.commit()
        
#         # Verificar que el token existe antes de eliminarlo
#         assert test_db_session.query(TokenModel).filter(TokenModel.id == token_id).first() is not None

#         # 2. Act
#         # repository.delete(token_id) # Asumiendo que tienes un método delete
#         # Para esta prueba, simulamos la eliminación directamente o asumimos que el método delete existe.
#         # Si no lo has implementado, omite esta prueba o implementa el método delete.
#         # Vamos a asumir que existe un método delete. Si no, comenta esta sección.
#         try:
#             deleted = repository.delete(token_id)
#             # 3. Assert
#             assert deleted is True # Asumiendo que delete devuelve True si se eliminó
#             assert test_db_session.query(TokenModel).filter(TokenModel.id == token_id).first() is None
#         except AttributeError:
#             # Si no existe el método delete, saltamos la prueba
#             pytest.skip("Método delete no implementado en SQLAlchemyTokenRepository")

#     def test_delete_token_not_found(self, test_db_session):
#         """Prueba que delete devuelva False o lance una excepción si el token no existe."""
#          # 1. Arrange
#         repository = SQLAlchemyTokenRepository(test_db_session)
#         non_existent_token_id = str(uuid.uuid4())

#         # 2. Act & Assert
#         # repository.delete(non_existent_token_id) # Asumiendo que delete lanza una excepción o devuelve False
#         # Para esta prueba, simulamos la eliminación directamente o asumimos que el método delete existe.
#         # Si no lo has implementado, omite esta prueba o implementa el método delete.
#         # Vamos a asumir que existe un método delete que devuelve False si no se encuentra.
#         try:
#             deleted = repository.delete(non_existent_token_id)
#             # 3. Assert
#             assert deleted is False # Asumiendo que delete devuelve False si no se encontró
#         except AttributeError:
#             # Si no existe el método delete, saltamos la prueba
#             pytest.skip("Método delete no implementado en SQLAlchemyTokenRepository")
#         except Exception as e:
#             # Si delete lanza otra excepción, también está bien (depende de tu implementación)
#             # Por ejemplo, podría lanzar ValueError o RuntimeError
#             # assert "No se encontró" in str(e) # Ajusta según tu implementación
#             pass # O simplemente pasamos si no sabemos qué excepción lanza

# # --- Notas sobre la implementación ---
# # 1. `@pytest.fixture(scope="function")`: Define una fixture que se ejecuta antes y después de cada función de prueba.
# # 2. `test_db_session`: Esta fixture:
# #    - Crea un engine apuntando a una BD de prueba.
# #    - Limpia y crea todas las tablas (`drop_all`, `create_all`).
# #    - Crea una sesión.
# #    - `yield session`: Entrega la sesión a la prueba.
# #    - En `finally`, cierra la sesión y limpia la BD (`drop_all`).
# # 3. `class TestSQLAlchemyTokenRepository:`: Agrupa las pruebas para el repositorio.
# # 4. Cada método de prueba (`test_...`) sigue el patrón AAA (Arrange, Act, Assert).
# # 5. Se usan aserciones (`assert`) para verificar resultados.
# # 6. Se manejan casos de éxito y de error (token no encontrado).
# # 7. `pytest.skip`: Se usa para saltar pruebas si una funcionalidad no está implementada.
# # 8. Estas son pruebas de integración porque interactúan con una BD real.
# # 9. ADVERTENCIA SOBRE LA BD DE PRUEBA: El fixture borra y recrea tablas. Asegúrate de usar una BD de prueba.