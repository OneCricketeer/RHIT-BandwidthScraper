from sqlalchemy import Column, ForeignKey, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
import datetime

Base = declarative_base()

class DbUsage(Base):
	__tablename__ = 'usage'
	id = Column(Integer, primary_key=True)
	policy_received = Column(Float(2))
	actual_received = Column(Float(2))
	policy_sent = Column(Float(2))
	actual_sent = Column(Float(2))
	timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class DbBandwidth(Base):
	__tablename__ = 'bandwidth'
	# __table_args__ = {'sqlite_autoincrement': True}
	id = Column(Integer, primary_key=True)
	bandwidth_class = Column(String(12))
	usage_id = Column(Integer, ForeignKey('usage.id'))

class DbBandwidthDevice(Base):
	__tablename__ = 'bandwidth_device'
	# __table_args__ = {'sqlite_autoincrement': True}
	id = Column(Integer, primary_key=True)
	# bandwidth = relationship("DbBandwidth", backref=backref('devices', order_by=id))
	net_addr = Column(String(17), unique=True)
	host = Column(String(50))
	comment = Column(String(50))

class DbBandwidthDeviceUsage(Base):
	__tablename__ = 'bandwidth_device_usage'
	__table_args__ = {'sqlite_autoincrement': True}
	id = Column(Integer, primary_key=True)
	bandwidth_id = Column(Integer, ForeignKey('bandwidth.id'))
	device_id = Column(Integer, ForeignKey('bandwidth_device.id'))
	usage_id = Column(Integer, ForeignKey('usage.id'))

engine = create_engine('sqlite:///bandwidth.db')
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)