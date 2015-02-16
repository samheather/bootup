# Candidate number: Y0073045

# Import Auth
from gluon.tools import Auth

# Create BootUp DB if necessary
db = DAL('sqlite://bootup.db')

# Setup BootUp tables needed for auth_user
'''
Countries is used to map a country name onto an ID that is referenced in Addresses.
An assumption is made that a country does not have a name longer than 100 characters.

CREATE TABLE Countries (
    id			INTEGER			PRIMARY KEY,
    country		VARCHAR(100)	NOT NULL
)

If the Countries table is empty, it will subsequently be populated with a set of 7
countries.
'''

db.define_table('Countries',
			Field('country', 'string', requires=IS_LENGTH(minsize=1, maxsize=100), required=True)
)

if db(db.Countries.id > 0).count() == 0:
	db.Countries.bulk_insert([
						{'country':'Australia'},
						{'country':'Canada'},
						{'country':'France'},
						{'country':'Germany'},
						{'country':'Switzerland'},
						{'country':'United Kingdom'},
						{'country':'United States of America'}])
	db.commit()

'''
Addresses is used to store the information for each address in the BootUp application, 
e.g. the street name, city, country and postal code.
An assumption is made that neither a streetAddress or city has a name longer than 100
characters.

CREATE TABLE Addresses (
    id				INTEGER			PRIMARY KEY,
    streetAddress	VARCHAR(100)	NOT NULL,
    city			VARCHAR(100)	NOT NULL,
    country			INTEGER			REFERENCES Countries (id),
    postalCode		VARCHAR(8)		NOT NULL
)
'''

db.define_table('Addresses',
			Field('streetAddress', 'string', label='Street Address', requires=IS_LENGTH(minsize=1, maxsize=100), required=True), \
			Field('city', 'string', requires=IS_LENGTH(minsize=1, maxsize=100), required=True), \
			Field('country', 'reference Countries', requires=IS_IN_DB(db, db.Countries.id, '%(country)s'), required=True), \
			Field('postalCode', 'string', label='Postal Code', requires=IS_LENGTH(minsize=6, maxsize=8), required=True)
)

'''
CreditCards is used to store the information for each Credit Card in the BootUp system.
This includes a reference to the billing address, the card number, expiry date and pin.

CREATE TABLE CreditCards (
    id				INTEGER			PRIMARY KEY,
    billingAddress	INTEGER			REFERENCES Addresses (id),
    cardNumber		VARCHAR(12)		NOT NULL,
    expiryDate		VARCHAR(5)		NOT NULL,
    pin				VARCHAR(3)		NOT NULL
)
'''

# TODO - set error message , error_message='Expiry Date must be in form MM/YY!' below
db.define_table('CreditCards',
			Field('billingAddress', db.Addresses), \
			Field('cardNumber', 'string', label='Card Number', requires=IS_LENGTH(minsize=12, maxsize=12), required=True), \
			Field('expiryDate', 'string', label='Expiry Date', requires=IS_LENGTH(minsize=4, maxsize=5), required=True), \
			Field('pin', 'string', label='Pin Number', requires=IS_LENGTH(minsize=3, maxsize=3), required=True)
)

# Setup Auth
'''
Here, the Web2Py Authentication tools are used.  These allow for easy use of
authentication (usernames, passwords etc) within the BootUp application.  The table for
representing users is called auth_user, and comes by default with some pre-set fields like
Name and Email address.  I will be adding birthdate, shippingAddress and paymentMethod to
this table, using "auth.settings.extra_fields[auth.settings.table_user_name] = []".

Since some of the fields already exist from the default web2py auth_user, I will show this
table below in DBDL/DDL as if I were creating it from scratch, as I have above for other
tables.  I shall ignore columns included from the auth_user that I don't use within the
BootUp application.

CREATE TABLE auth_user (
    id				INTEGER			PRIMARY KEY,
    first_name		VARCHAR(128)	NOT NULL,
    last_name		VARCHAR(128)	NOT NULL,
    email			VARCHAR(512)	NOT NULL,
    username		VARCHAR(128)	NOT NULL,
    password		VARCHAR(512)	NOT NULL,
    birthdate		VARCHAR(10)		NOT NULL,
    shippingAddress	INTEGER			REFERENCES Addresses (id),
    paymentMethod	INTEGER			REFERENCES CreditCards (id)
)
'''

# TODO - set error message , error_message='Birthdate must be in form DD/MM/YYYY' below
auth = Auth(db, controller='default/auth_user')
auth.settings.extra_fields[auth.settings.table_user_name] = [
	Field('birthdate', 'string', label='Date of Birth', requires=IS_LENGTH(minsize=8, maxsize=10), required=True),
	Field('shippingAddress', db.Addresses),
	Field('paymentMethod', db.CreditCards)
    ]
auth.settings.login_url = URL(request.application,'default','login')
auth.settings.logout_next = URL('default', 'index')
auth.settings.register_next = URL('default', args='index')
auth.define_tables(username=True,signature=False)

# Setup rest of BootUp tables
'''
Categories is used to map a category name onto an ID that is referenced in a Bootable.
An assumption is made that a Category does not have a name longer than 50 characters.

CREATE TABLE Categories (
    id			INTEGER			PRIMARY KEY,
    category	VARCHAR(50)		NOT NULL
)

If the Categories table is empty, it will subsequently be populated with a set of 9
categories.
'''

db.define_table('Categories',
			Field('category', 'string', requires=IS_LENGTH(minsize=1, maxsize=50), required=True)
)

if db(db.Categories.id > 0).count() == 0:
	db.Categories.bulk_insert([
						{'category':'Art'},
						{'category':'Comics'},
						{'category':'Crafts'},
						{'category':'Fashion'},
						{'category':'Film'},
						{'category':'Games'},
						{'category':'Music'},
						{'category':'Photography'},
						{'category':'Technology'}])
	db.commit()

'''
States is used to map a state name onto an ID that is referenced in a Bootable.
An assumption is made that a State does not have a name longer than 25 characters.

CREATE TABLE States (
    id			INTEGER			PRIMARY KEY,
    state		VARCHAR(25)		NOT NULL
)

If the States table is empty, it will subsequently be populated with the 4 possible state
names and their ID's.
'''

db.define_table('States',
			Field('state', 'string', requires=IS_LENGTH(minsize=1, maxsize=25), required=True)
)

if db(db.States.id > 0).count() == 0:
	db.States.bulk_insert([
						{'id':-1, 'state':'Not Available'},
						{'id':0, 'state':'Open'},
						{'id':1, 'state':'Funded'},
						{'id':2, 'state':'Not Funded'}])
	db.commit()

'''
The Bootables table is used to store all the information for a single Bootable.  This
includes the Bootable title, shortDescription, longDescription, category, the funding
goal, an image path, a long description, information on the manager, the date the bootable
was created and it's state.

An assumption that is made is that a title will not have a length longer than 60
characters.

Image is stored as text.  This is because of the way that the web2py dal/field helper
handles uploads.  It takes the uploaded file and stores it in a special uploads directory
with a safe file name (one that can not cause security problems because it contains
special characters etc).  This file name is then stored in the image TEXT field, so a path
can later be constructed to retrieve the image.  More can be read on this in the Web2Py
book, here:
http://www.web2py.com/books/default/chapter/29/06/the-database-abstraction-layer#Field-types

CREATE TABLE Bootables (
    id					INTEGER			PRIMARY KEY,
    user_id				INTEGER			REFERENCES auth_user (id),
    title				VARCHAR(60)	NOT NULL,
    shortDescription	VARCHAR(120)	NOT NULL,
    category			INTEGER			REFERENCES Categories (id),
    fundingGoal			INTEGER			NOT NULL,
    image				TEXT			NOT NULL,
    longDescription		TEXT			NOT NULL,
    managerInfo			TEXT			NOT NULL,
    dateCreated			TIMESTAMP		NOT NULL,
	state				INTEGER			REFERENCES States (id)
)
'''

db.define_table('Bootables',
			Field('user_id', db.auth_user), \
			Field('title', 'string', requires=IS_LENGTH(minsize=1, maxsize=60), required=True), \
			Field('shortDescription', 'string', label='Short Description', requires=IS_LENGTH(minsize=1, maxsize=120), required=True), \
			Field('category', 'reference Categories', requires=IS_EMPTY_OR(IS_IN_DB(db, db.Categories.id, '%(category)s')), required=True), \
			Field('fundingGoal', 'integer', label='Funding Goal', required=True), \
			Field('image', 'upload'), \
			Field('longDescription', 'text', label='Long Description', required=True), \
			Field('managerInfo', 'text', label='Bootable Manager Information', required=True), \
			Field('dateCreated', 'datetime', required=True), \
			Field('state', db.States, required=True), \
)

'''
The Rewards table is used to store each Reward row.  These are associated with a Bootable
and contain a string representation of the reward offered.

Reward has a maximum length of 256, which is potentially much longer than may be needed,
however in the rare event that the Bootable manager needs to put additional shipping
information for a specific reward, this will allow them the flexibility to do so.

CREATE TABLE Rewards (
    id					INTEGER			PRIMARY KEY,
    bootable_id			INTEGER			REFERENCES Bootables (id),
	reward				VARCHAR(256)	NOT NULL
)
'''

db.define_table('Rewards',
			Field('bootable_id', db.Bootables, required=True), \
			Field('reward', 'string', label='Reward Description', requires=IS_LENGTH(minsize=1, maxsize=256), required=True)
)

'''
The PledgeOptions table is used to store each PledgeOption row.  These are associated with
a Bootable and contain a string representation of the title of the Pledge, a value for 
the price of the PledgeOption.  

The reward field is present to allow easy generation of the multi-select field used in the
SQLFORM for adding rewards to a PledgeOption.  However it is never set - it remains null
as rewards to PledgeOptions are stored in the PledgeRewardPairs table below (because the 
relationship is a many-to-many relationship).

pledgeTitle is limited to 60 characters in length.  This is because it should only be a 
short name for the collection of rewards it corresponds to.

CREATE TABLE PledgeOptions (
    id				INTEGER			PRIMARY KEY,
    bootable_id		INTEGER			REFERENCES Bootables (id),
	pledgeTitle		VARCHAR(60)		NOT NULL,
	price			INTEGER			NOT NULL,
	reward			VARCHAR(512)
)
'''

db.define_table('PledgeOptions',
			Field('bootable_id', db.Bootables, required=True), \
			Field('pledgeTitle', 'string', label='Pledge Option Title', requires=IS_LENGTH(minsize=1, maxsize=60), required=True), \
			Field('price', 'integer', required=True), \
			Field('reward', 'list:reference Rewards', label='Rewards (Hold CTRL/Command to select multiple)')
)

'''
The PledgeRewardPairs table is used to represent the many-to-many relationship between
a PledgeOption and the rewards included in that option (bearing in mind that a reward can
be included in multiple PledgeOptions).  Each row represents one such pairing, with a
reference to a reward paired with a reference to a PledgeOption.

CREATE TABLE PledgeRewardPairs (
    id				INTEGER			PRIMARY KEY,
    reward_id		INTEGER			REFERENCES Rewards (id),
    pledgeOption_id	INTEGER			REFERENCES PledgeOptions (id)
)
'''

db.define_table('PledgeRewardPairs',
			Field('reward_id', db.Rewards, required=True), \
			Field('pledgeOption_id', db.PledgeOptions, required=True)
)

'''
The Pledges table represents the pledges that are made by users.  Pledges are made from 
a user to a Bootable.  Each row in this table contains a reference to a user and a
reference to a pledge (i.e. that a user has pledged to this PledgeOption).

CREATE TABLE Pledges (
    id			INTEGER		PRIMARY KEY,
    user_id		INTEGER		REFERENCES auth_user (id),
    pledge_id	INTEGER		REFERENCES PledgeOptions (id)
)
'''

db.define_table('Pledges',
			Field('user_id', db.auth_user, required=True), \
			Field('pledge_id', db.PledgeOptions, required=True)
)

'''
An SQL View is used below for listing the rewards attached to each PledgeOption in a single
query.  It uses GROUP_CONCAT and GroupBy to group multiple rows into one with a delimited
list of rewards.
'''

# Dummy tables - Web2Py forces me to create this to create an object in the DAL to then be
# able to query the below SQL view.
db.define_table('RewardsForEachPledgeOption',
    Field('bootable_id'),
    Field('price'),
    Field('pledgeTitle'),
    Field('reward_id'),
    Field('pledgeOption_id'),
    Field('reward'),
    Field('rewardsForThisPledgeOption'),
    migrate=False)
    
# Create View to list rewards for each PledgeOption
db.executesql('CREATE VIEW IF NOT EXISTS RewardsForEachPledgeOption AS SELECT PledgeOptions.id, PledgeOptions.bootable_id, PledgeOptions.pledgeTitle, PledgeOptions.price, PledgeRewardPairs.reward_id, PledgeRewardPairs.pledgeOption_id, Rewards.id, Rewards.reward, GROUP_CONCAT(Rewards.reward) rewardsForThisPledgeOption FROM PledgeOptions, Rewards, PledgeRewardPairs WHERE PledgeOptions.id == PledgeRewardPairs.pledgeOption_id AND PledgeRewardPairs.reward_id == Rewards.id GROUP BY PledgeOption_id')
    
'''
An SQL View is used below for calculating the total raised and the percentage this is of
the target fundingGoal of each Bootable.  It includes all of the information for a 
Bootable so that a Row of this View can be used standalone in the ViewBootable View, 
without a separate row from Bootables.
'''    

# Dummy tables - Web2Py forces me to create this to create an object in the DAL to then be
# able to query the below SQL view.
db.define_table('BootablesWithTotalPledged',
    Field('id'),
	Field('user_id'),
	Field('title'),
	Field('shortDescription'),
	Field('category'),
	Field('fundingGoal'),
	Field('image', 'upload'),
	Field('longDescription'),
	Field('managerInfo'),
	Field('dateCreated'),
	Field('state', 'integer'),
    Field('raised'),
    Field('percentageComplete', 'integer'),
    migrate=False)

# Create view to sum the total raised for each bootable.
db.executesql('CREATE VIEW IF NOT EXISTS BootablesWithTotalPledged AS SELECT * FROM Bootables LEFT JOIN (SELECT Bootables.id, SUM(PledgeOptions.price) AS raised, SUM(PledgeOptions.price)*100 / Bootables.fundingGoal AS percentageComplete FROM Pledges LEFT JOIN PledgeOptions ON Pledges.pledge_id=PledgeOptions.id LEFT JOIN Bootables ON Bootables.id=PledgeOptions.bootable_id GROUP BY PledgeOptions.bootable_id) totals ON totals.id=Bootables.id;')

# Check if user has filled in address and credit card, so can force user back to Address
# and Credit Card pages if they are half way through registering
response.userNeedsToEnterShippingAddress=False
response.userNeedsToEnterPaymentInfo=False
if (auth.user != None):
	user = db.auth_user(auth.user.id)
	if (user.shippingAddress == None):
		response.userNeedsToEnterShippingAddress = True
	elif (user.paymentMethod == None):
		response.userNeedsToEnterPaymentInfo = True