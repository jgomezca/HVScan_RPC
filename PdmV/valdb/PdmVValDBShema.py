#-mo TODO: Properly explain that this script is used to create the schema
#           in the development DB.

from sqlalchemy import create_engine, DateTime, MetaData, Column, Table, ForeignKey, Integer, String , Sequence, Boolean
from ConStrParser import *

connectionDictionary = service.getSecrets()['connections']['dev']
engine = create_engine(service.getSqlAlchemyConnectionString(connectionDictionary), echo=False)
 
metadata = MetaData(bind=engine)

releases_table = Table('releases', metadata,
                    Column('id', Integer, Sequence('releases_id_seq'), primary_key=True, nullable=False),
                    Column('category', String(40), nullable=False),
                    Column('subcategory', String(40), nullable=False),
                    Column('release_name', String(100), nullable=False),
                    Column('version', Integer, nullable=False),
                    Column('date', DateTime, nullable=False),
                    Column('status_kind', String(20), nullable=False))
                    
releases_lv_table = Table('releases_lv', metadata,
                    Column('id', Integer, primary_key=True, nullable=False),
                    Column('category', String(40), nullable=False),
                    Column('subcategory', String(40), nullable=False),
                    Column('release_name', String(100), nullable=False),
                    Column('version', Integer, nullable=False),
                    Column('date', DateTime, nullable=False),
                    Column('status_kind', String(20), nullable=False))

status_table = Table('status', metadata,
                    Column('id', Integer, ForeignKey("releases.id"), primary_key=True, nullable=False),
                    Column('validation_status', String(50), default="NOT YET DONE", nullable=False),
                    Column('comments', String(2000)),
                    Column('links', String(1000)),
                    Column('user_name', String(100), nullable=False))
                    
status_lv_table = Table('status_lv', metadata,
                    Column('id', Integer, ForeignKey("releases_lv.id"), primary_key=True, nullable=False),
                    Column('validation_status', String(50), default="NOT YET DONE", nullable=False),
                    Column('comments', String(2000)),
                    Column('links', String(1000)),
                    Column('user_name', String(100), nullable=False))
                   
users_table = Table('users', metadata,
                    Column('user_name', String(100), nullable=False, primary_key=True),
                    Column('email', String(50)),
                    Column('admin', Boolean, default=False),
                    Column('validator', Boolean, default=False))
                
user_rights_table = Table('user_rights', metadata,
                    Column('id', Integer, Sequence('id_seq'), primary_key=True, nullable=False),
                    Column('user_name', String(100), ForeignKey('users.user_name'), nullable=False),
                    Column('category', String(40), nullable=False),
		    Column('subcategory', String(40), nullable=False),
                    Column('status_kind', String(20), nullable=False))
                    
metadata.create_all()
