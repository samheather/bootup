def notNone(input):
	for row in input:
		if row.BootablesWithTotalPledged.percentageComplete == None:
			row.BootablesWithTotalPledged.percentageComplete = 0
		if row.BootablesWithTotalPledged.raised == None:
			row.BootablesWithTotalPledged.raised = 0
	return input
