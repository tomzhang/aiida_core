# -*- coding: utf-8 -*-

import json

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Boolean, Text
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sqlalchemy.dialects.postgresql import UUID, JSONB

from aiida.backends.sqlalchemy.models.base import Base
from aiida.backends.sqlalchemy.models.utils import uuid_func

from aiida.common.exceptions import NotExistent, DbContentError, ConfigurationError


class DbComputer(Base):
    __tablename__ = "db_dbcomputer"

    id = Column(Integer, primary_key=True)

    uuid = Column(UUID(as_uuid=True), default=uuid_func)
    name = Column(String(255), unique=True, nullable=False)
    hostname = Column(String(255))

    description = Column(Text, nullable=True)
    enabled = Column(Boolean)

    transport_type = Column(String(255))
    scheduler_type = Column(String(255))

    transport_params = Column(JSONB)
    _metadata = Column('metadata', JSONB)

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self._metadata = {}
        self.transport_params = {}
        super(DbComputer, self).__init__(*args, **kwargs)

    @classmethod
    def get_dbcomputer(cls, computer):
        """
        Return a DbComputer from its name (or from another Computer or DbComputer instance)
        """

        from aiida.orm.computer import Computer
        if isinstance(computer, basestring):
            try:
                dbcomputer = cls.query(name=computer).one()
            except NoResultFound:
                raise NotExistent("No computer found in the table of computers with "
                                  "the given name '{}'".format(computer))
            except MultipleResultsFound:
                raise DbContentError("There is more than one computer with name '{}', "
                                     "pass a Computer instance".format(computer))

        elif isinstance(computer, DbComputer):
            if computer.id is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer
        elif isinstance(computer, Computer):
            if computer.dbcomputer.id is None:
                raise ValueError("The computer instance you are passing has not been stored yet")
            dbcomputer = computer.dbcomputer
        else:
            raise TypeError("Pass either a computer name, a DbComputer django instance or a Computer object")
        return dbcomputer

    def get_workdir(self):
        try:
            return self._metadata['workdir']
        except KeyError:
            raise ConfigurationError('No workdir found for DbComputer {} '.format(
                self.name))


    def __str__(self):
        if self.enabled:
            return "{} ({})".format(self.name, self.hostname)
        else:
            return "{} ({}) [DISABLED]".format(self.name, self.hostname)
