# -*- coding: utf-8 -*-
# Candidate number: Y0073045

import datetime

from bootup import notNone

def index():
	newestFiveBootables = db(db.BootablesWithTotalPledged.state == 0).select(orderby=~db.BootablesWithTotalPledged.dateCreated)[0:5]
	newestFiveBootables.compact = False
	newestFiveBootables = notNone(newestFiveBootables)
	
	closestFiveToFunded = db(
						(db.BootablesWithTotalPledged.state == 0) & \
						((db.BootablesWithTotalPledged.percentageComplete < 100) |
						(db.BootablesWithTotalPledged.percentageComplete == None))).select(orderby=~db.BootablesWithTotalPledged.percentageComplete)[0:5]
	closestFiveToFunded.compact = False
	closestFiveToFunded = notNone(closestFiveToFunded)
	
	return dict(newestFiveBootables=newestFiveBootables,
				closestFiveToFunded=closestFiveToFunded)
	
@auth.requires_login()
def new():
	# Hide user_id field, create the table, then populate user_id field
	db.Bootables.user_id.readable = db.Bootables.user_id.writable = False
	db.Bootables.dateCreated.readable = db.Bootables.dateCreated.writable = False
	db.Bootables.state.readable = db.Bootables.state.writable = False
	form = SQLFORM(db.Bootables, record=None, formstyle="bootstrap3_stacked")
	form.vars.user_id = auth.user.id
	form.vars.dateCreated = datetime.datetime.utcnow()
	form.vars.state = -1
	if form.accepts(request,session):
		redirect(URL('default', 'editPledge', args=form.vars.id))
	elif form.errors:
		response.flash = 'One or more of your form fields has an error. Please see below for more information'
	
	return dict(form=form)

@auth.requires_login()	
def addPledge():
	newBootableRecord = db((db.Bootables.user_id == auth.user.id)).select(db.Bootables.ALL).as_list()[-1]
	addPledgeForm = SQLFORM(db.PledgeOptions, record=None, formstyle="bootstrap3_stacked", fields=['reward_title', 'reward_description', 'price'])
	addPledgeForm.vars.bootable_id = newBootableRecord['id']
	
	if addPledgeForm.accepts(request,session):
		response.flash = 'Pledge option added'
	elif addPledgeForm.errors:
		response.flash = 'One or more of your form fields has an error. Please see below for more information'
	else:
		response.flash = 'Please complete the form below to create a new bootable.'
	
	return dict(addPledgeForm=addPledgeForm)

@auth.requires_login()
def editBootable():
	bootableId = request.args(0)
	if (bootableId != None):
		# Get the bootable record
		bootableRecord=db.Bootables(bootableId)
		# Hide user_id field and create the table (using the bootable record)
		db.Bootables.user_id.readable = db.Bootables.user_id.writable = False
		db.Bootables.dateCreated.readable = db.Bootables.dateCreated.writable = False
		db.Bootables.state.readable = db.Bootables.state.writable = False
		db.Bootables.id.readable = db.Bootables.id.writable = False
		editBootableForm = SQLFORM(db.Bootables, record=bootableRecord, formstyle="bootstrap3_stacked")
	
		if editBootableForm.accepts(request,session):
			response.flash = 'Your changes have been saved.'
		elif editBootableForm.errors:
			response.flash = 'One or more of your form fields has an error. Please see below for more information'
		else:
			response.flash = 'Please complete the form below to edit your bootable.'

		return dict(editBootableForm=editBootableForm)

@auth.requires_login()	
def editPledge():
	bootable_id=request.args(0)
	db.Rewards.bootable_id.readable = db.Rewards.bootable_id.writable = False
	rewardsForm = SQLFORM(db.Rewards, record=None, formstyle="bootstrap3_stacked")
	rewardsForm.vars.bootable_id=bootable_id
	if rewardsForm.accepts(request,session):
		pass
	elif rewardsForm.errors:
		response.flash = 'One or more of your form fields has an error. Please see below for more information'
	else:
		response.flash = 'Add rewards below'
		
	db.PledgeOptions.bootable_id.readable = db.PledgeOptions.bootable_id.writable = False
	db.PledgeOptions.reward.requires = IS_IN_DB(db(db.Rewards.bootable_id==bootable_id), db.Rewards.id, '%(reward)s', multiple=True)
	addPledgeForm = SQLFORM.factory(db.PledgeOptions, record=None, formstyle="bootstrap3_stacked")
	addPledgeForm.vars.bootable_id=request.args(0)
	if addPledgeForm.accepts(request,session):
		pledgeId = db.PledgeOptions.insert(
										bootable_id=addPledgeForm.vars.bootable_id,
										price=addPledgeForm.vars.price,
										pledgeTitle=addPledgeForm.vars.pledgeTitle)
		rewardsSelected = addPledgeForm.vars.reward
		for rewardSelected in rewardsSelected:
			db.PledgeRewardPairs.insert(reward_id=rewardSelected,pledgeOption_id=pledgeId)
	elif addPledgeForm.errors:
		response.flash = 'One or more of your form fields has an error. Please see below for more information'
	else:
		response.flash = 'Add Possible Pledges Below'
		
	existingRewards = db(db.Rewards.bootable_id == bootable_id).select()
	existingPledgeOptions = db(db.RewardsForEachPledgeOption.bootable_id == bootable_id).select()
	rewardsInPledgesQuery = db(db.PledgeRewardPairs).select()
	rewardsInPledges = []
	for rewardInPledges in rewardsInPledgesQuery:
		rewardsInPledges.append(rewardInPledges.reward_id)
	
	thisBootable=db(db.Bootables.id == request.args(0)).select().first()
	
	return dict(rewardsForm=rewardsForm,
				addPledgeForm=addPledgeForm,
				existingRewards=existingRewards,
				existingPledgeOptions=existingPledgeOptions,
				rewardsInPledges=rewardsInPledges,
				thisBootable=thisBootable)	
			
# 	pledgeOption = request.args(0)
# 	if (pledgeOption == None):
# 		pledgeForm = SQLFORM(db.PledgeOptions, record=None, formstyle="bootstrap3_stacked", fields=['reward_title', 'reward_description', 'price'])
# 	else:
# 		db.PledgeOptions.id.readable = db.PledgeOptions.id.writable = False
# 		pledgeRecord=db.PledgeOptions(pledgeOption)
# 		pledgeForm = SQLFORM(db.PledgeOptions, record=pledgeRecord, formstyle="bootstrap3_stacked", fields=['reward_title', 'reward_description', 'price'])
# 	return dict(pledgeForm=pledgeForm)

@auth.requires_login()
def editReward():
	bootable_id = request.args(0)
	reward_id = request.args(1)
	db.Rewards.id.readable = db.Rewards.id.writable = False
	rewardRecord = db.Rewards(reward_id)
	rewardForm = SQLFORM(db.Rewards, record=rewardRecord, formstyle="bootstrap3_stacked", fields=["reward"])
	
	if rewardForm.accepts(request,session):
		redirect(URL('default', 'editPledge', args=bootable_id))
	elif rewardForm.errors:
		response.flash = 'Rewards must have a description.'
	
	return dict(rewardForm=rewardForm)

@auth.requires_login()	
def deleteReward():
	bootable_id = request.args(0)
	reward_id = request.args(1)
	db(db.Rewards.id == reward_id).delete()
	redirect(URL('default', 'editPledge', args=bootable_id))

@auth.requires_login()
def deletePledge():
	bootable_id = request.args(0)
	pledgeOption_id = request.args(1)
	db(db.PledgeRewardPairs.pledgeOption_id==pledgeOption_id).delete()
	db(db.PledgeOptions.id==pledgeOption_id).delete()
	redirect(URL('default', 'editPledge', args=bootable_id))

@auth.requires_login()
def deleteBootable():
	bootable_id = request.args(0)
	pledgeOptionsForThisBootableQuery = db(db.PledgeOptions.bootable_id==bootable_id).select()
	pledgeOptionsForThisBootable = []
	for pledgeOptionForThisBootable in pledgeOptionsForThisBootableQuery:
		pledgeOptionsForThisBootable.append(pledgeOptionForThisBootable.id)
	# Delete rewards for this Bootable
	db(db.Rewards.bootable_id == bootable_id).delete()
	for pledgeOption in pledgeOptionsForThisBootable:
		# Delete PledgeRewardPairs for this PledgeOption for this Bootable
		db(db.PledgeRewardPairs.pledgeOption_id == pledgeOption).delete()
		# Delete Pledges for this PledgeOption for this Bootable
		db(db.Pledges.pledge_id == pledgeOption).delete()
	# Delete the PledgeOptions for this Bootable
	db(db.PledgeOptions.bootable_id == bootable_id).delete()
	# Delete this bootable
	db(db.Bootables.id == bootable_id).delete()
	redirect(URL('user', 'profile'))

def category():
	bootables = db((db.BootablesWithTotalPledged.category==db.Categories.id) & (db.Categories.category == request.args(0))).select()
	bootables=notNone(bootables)
	return dict(bootables=bootables)
	
def download():
	return response.download(request, db)
	
def search():
	searchTerm="%"+request.vars.searchTerm+"%"
	# TODO - add search for shortDescription as well, these items should be lower priority though.  Sort by date created.
	bootables = db(
				(db.BootablesWithTotalPledged.state >= 0) & \
				(db.BootablesWithTotalPledged.title.like(searchTerm))).select()
	bootables.compact = False
	bootables=notNone(bootables)
	return dict(bootables=bootables)
	
def view():
	bootable = db((db.BootablesWithTotalPledged.category==db.Categories.id) & \
		(db.BootablesWithTotalPledged.id == request.args(0))).select()
	bootable=notNone(bootable)
	bootable=notNone(bootable).first()
		
	possiblePledgeOptions = db(
		(db.PledgeOptions.bootable_id==request.args(0))).select()
	processedPossiblePledges = []
	for possiblePledgeOption in possiblePledgeOptions:
		pledgeWithRewards = db(
			(db.PledgeRewardPairs.pledgeOption_id==possiblePledgeOption.id) & \
			(db.PledgeRewardPairs.reward_id==db.Rewards.id)).select()
		rewards=[]
		for row in pledgeWithRewards:
			rewards.append(row.Rewards.reward)
		processedPossiblePledges.append({
									'pledgeOption_id':possiblePledgeOption.id,
									'price':possiblePledgeOption.price,
									'pledgeTitle':possiblePledgeOption.pledgeTitle,
									'rewards':rewards
									})
		
	usersAndPledges = db((db.Bootables.id==db.PledgeOptions.bootable_id) & \
		(db.Bootables.id == request.args(0)) & \
		(db.Pledges.user_id == db.auth_user.id) & \
		(db.Pledges.pledge_id == db.PledgeOptions.id)).select()
	
	userIsLoggedIn = False
	if (auth.user != None):
		userIsLoggedIn=True
		
	pledgesFromThisUserForThisBootable=None
	if (userIsLoggedIn):
		pledgesFromThisUserForThisBootableQuery = db((db.Bootables.id==db.PledgeOptions.bootable_id) & \
			(db.Bootables.id == request.args(0)) & \
			(db.Pledges.user_id == db.auth_user.id) & \
			(db.Pledges.user_id == auth.user.id) & \
			(db.Pledges.pledge_id == db.PledgeOptions.id)).select()
		if (len(pledgesFromThisUserForThisBootableQuery)>0):
			pledgesFromThisUserForThisBootable = pledgesFromThisUserForThisBootableQuery[0]
	
	return dict(
		bootable=bootable,
		processedPossiblePledges=processedPossiblePledges,
		usersAndPledges=usersAndPledges,
		userIsLoggedIn=userIsLoggedIn,
		pledgesFromThisUserForThisBootable=pledgesFromThisUserForThisBootable,
	)
	
@auth.requires_login()
def launchOrRelaunch():
	bootableId=request.args(0)
	db(db.Bootables.id==bootableId).update(state=0)
	if (request.args(1) == "view"):
		redirect(URL('default','view',args=request.args(0)))
	else:
		redirect(URL('user','profile'))
		
@auth.requires_login()
def close():
	bootableId=request.args(0)
	bootableRecord = db(db.BootablesWithTotalPledged.id==bootableId).select().first()
	if (bootableRecord.percentageComplete < 100 or bootableRecord.percentageComplete == None):
		db(db.Bootables.id==bootableId).update(state=2)
	else:
		db(db.Bootables.id==bootableId).update(state=1)
	if (request.args(1) == "view"):
		redirect(URL('default','view',args=request.args(0)))
	else:
		redirect(URL('user','profile'))

@auth.requires_login()
def boot():
	# Delete previous pledges for this user on this bootable
	pledgesFromThisUserForThisBootableQuery = db((db.Bootables.id==db.PledgeOptions.bootable_id) & \
			(db.Bootables.id == request.args(0)) & \
			(db.Pledges.user_id == db.auth_user.id) & \
			(db.Pledges.user_id == auth.user.id) & \
			(db.Pledges.pledge_id == db.PledgeOptions.id)).select()
	for pledge in pledgesFromThisUserForThisBootableQuery:
		db(db.Pledges.id == pledge.Pledges.id).delete()
		
	# Make the pledge
	bootable = request.args(0)
	pledge_id = request.args(1)
	user_id = auth.user.id
	db.Pledges.insert(user_id=user_id, pledge_id=pledge_id)
	
	# Send user back to the bootable, now they've made their pledge.
	redirect(URL('default', 'view', args=bootable))
	
def auth_user():
	auth.settings.formstyle = 'bootstrap3_stacked'

	# Shipping and billing addresses are edited elsewhere in the application.  We never
	# show ID since it is a unique primary key.  
	
	# Originally it was assumed Birthdate would never change.  This is because a user may
	# try and make their birthdate earlier in the past after realising that they don't
	# qualify for some parts of the application (e.g. because they are under the age of
	# 18).  This was achieved by simply setting the Birthdate attribute readable and 
	# writeable to False, as has been done below with ID.
	# The decision was not taken, since the assessment document says that a user should be
	# able to chance all information stored on them.
	
	db.auth_user.shippingAddress.readable = db.auth_user.shippingAddress.writable = False
	db.auth_user.paymentMethod.readable = db.auth_user.paymentMethod.writable = False
	db.auth_user.id.readable = db.auth_user.id.writable = False

	# Set redirect URL for after logging-in to the page that the user was on before (if
	# this variable was passed in).	
	auth.settings.login_next = request.vars['_next']

	return dict(form=auth())