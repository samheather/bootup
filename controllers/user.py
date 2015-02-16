# -*- coding: utf-8 -*-
# Candidate number: Y0073045

from bootup import notNone
	
def register():
	if (request.args(0)=='shipping_address'):
		form=SQLFORM(db.Addresses, formstyle="bootstrap3_stacked")
		form.custom.widget.postalCode.update(_placeholder="YO10 5DD")
		page=2
		if form.accepts(request,session):
			addressId = form.vars.id
			db(db.auth_user.id == auth.user.id).update(shippingAddress=addressId)
			redirect(URL('user','register', args="payment_method"))
		elif form.errors:
			response.flash = 'form has errors'
		else:
			response.flash = 'please fill the form'
	elif (request.args(0)=='payment_method'):
		db.CreditCards.billingAddress.readable = db.CreditCards.billingAddress.writable = False
		form=SQLFORM.factory(db.CreditCards, db.Addresses, formstyle="bootstrap3_stacked")
		shippingAddress=db.Addresses(db.auth_user(auth.user.id).shippingAddress)
		form.vars.streetAddress = shippingAddress.streetAddress
		form.vars.city = shippingAddress.city
		form.vars.country = shippingAddress.country
		form.vars.postalCode = shippingAddress.postalCode
		form.custom.widget.expiryDate.update(_placeholder="06/18")
		page=3
		if form.accepts(request,session):
			id = db.Addresses.insert(**db.Addresses._filter_fields(form.vars))
			form.vars.billingAddress=id
			paymentMethodId = db.CreditCards.insert(**db.CreditCards._filter_fields(form.vars))
 			db(db.auth_user.id == auth.user.id).update(paymentMethod=paymentMethodId)
 			redirect(URL('default','index'))
		elif form.errors:
			form.errors.cardNumber = 'Card Number must be 12 numbers.'
			form.errors.pin = 'Pin must be 3 numbers.'
			response.flash = 'form has errors'
		else:
			response.flash = 'please fill the form'
	else:
		auth.settings.formstyle="bootstrap3_stacked"
		auth.settings.register_next = URL('user/register','shipping_address')
		db.auth_user.shippingAddress.readable=db.auth_user.shippingAddress.writable=False
		db.auth_user.paymentMethod.readable=db.auth_user.paymentMethod.writable=False
		form=auth.register()
		form.elements('.w2p_fl', replace=None)
		form.custom.widget.birthdate.update(_placeholder="01/01/1970")
		page=1
    
	return dict(form=form,page=page)

@auth.requires_login()	
def profile():
	# Generate a list, myBootablesIdsWithPledgeOptions, of Bootable project ID's that have
	# PledgeOptions attached to them and so are launchable.
	myPledgeOptions=db((db.PledgeOptions.bootable_id == db.Bootables.id) & \
						(db.Bootables.user_id == auth.user.id)).select()
	myBootablesIdsWithPledgeOptions = []
	for pledgeOption in myPledgeOptions:
		myBootablesIdsWithPledgeOptions.append(pledgeOption.Bootables.id)

	myPledgeOptionsAndRewards = db(
						(db.BootablesWithTotalPledged.id == db.RewardsForEachPledgeOption.bootable_id) & \
						(db.Pledges.user_id == auth.user.id) & \
						(db.BootablesWithTotalPledged.state == db.States.id) & \
						(db.RewardsForEachPledgeOption.pledgeOption_id == db.Pledges.pledge_id)).select()
	myPledgeOptionsAndRewards=notNone(myPledgeOptionsAndRewards)
						
	myBootables = db(
				(db.BootablesWithTotalPledged.category==db.Categories.id) & \
				(db.BootablesWithTotalPledged.user_id == auth.user.id) & \
				(db.BootablesWithTotalPledged.state == db.States.id)).select()
	myBootables=notNone(myBootables)
	
	return dict(
			numberOfPledges=getNumberOfPledges(),
			totalPledged=getAmountPledged(),
			myBootablesIdsWithPledgeOptions=myBootablesIdsWithPledgeOptions,
			myPledgeOptionsAndRewards=myPledgeOptionsAndRewards,
			myBootables=myBootables)

@auth.requires_login()		
def accountDetails():
	shippingAddressId=db.auth_user(auth.user.id).shippingAddress
	shippingAddress=db((db.Addresses.id == shippingAddressId) & \
						(db.Addresses.country == db.Countries.id)).select().first()
	billingAddressId=db((db.auth_user.paymentMethod==db.CreditCards.id)).select().first().CreditCards.billingAddress
	billingAddress=db((db.Addresses.id == billingAddressId) & \
						(db.Addresses.country == db.Countries.id)).select().first()
	creditCardId=db.auth_user(auth.user.id).paymentMethod
	creditCard=db.CreditCards(creditCardId)
	
	userRecord = db.auth_user(auth.user.id)
	
	return dict(
			numberOfPledges=getNumberOfPledges(),
			totalPledged=getAmountPledged(),
			shippingAddress=shippingAddress,
			billingAddress=billingAddress,
			creditCard=creditCard,
			userRecord=userRecord)
			
def getNumberOfPledges():
	allPledgesMade = db((db.Pledges.pledge_id==db.PledgeOptions.id) & (db.Pledges.user_id == auth.user.id))
	return allPledgesMade.count()
	
def getAmountPledged():
	sumSpecification=db.PledgeOptions.price.sum()
	row = db(
		(db.Pledges.pledge_id==db.PledgeOptions.id) & \
		(db.Pledges.user_id == auth.user.id) \
		).select(sumSpecification).first()
	sum = row[sumSpecification]
	if (sum==None):
		sum=0
	return sum

@auth.requires_login()	
def editProfile():
	if (request.args(0) == 'Address'):
		addressId=request.args(1)
		editTitle='Edit Billing Address'
		if (len(db(db.auth_user.shippingAddress==addressId).select())>0):
			editTitle='Edit Shipping Address'
		addressRecord=db.Addresses(addressId)
		db.Addresses.id.readable = db.Addresses.id.writable = False
		form=SQLFORM(db.Addresses, record=addressRecord, formstyle="bootstrap3_stacked")
	elif (request.args(0) == 'CreditCard'):
		cardId = request.args(1)
		editTitle='Edit Credit Card'
		cardRecord=db.CreditCards(cardId)
		db.CreditCards.id.readable = db.CreditCards.id.writable = False
		db.CreditCards.billingAddress.readable = db.CreditCards.billingAddress.writable = False
		form=SQLFORM(db.CreditCards, record=cardRecord, formstyle="bootstrap3_stacked")
	
	if form.accepts(request,session):
		redirect(URL('user','accountDetails'))
	
	return dict(editTitle=editTitle,form=form)