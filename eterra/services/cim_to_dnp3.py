import json
import logging
import sys
import time


from gridappsd.topics import fncs_input_topic, fncs_output_topic


out_json=list()

# attribute mapping for control points
attribute_map = {
    "capacitors" : {
        "attribute" : ["RegulatingControl.mode","RegulatingControl.targetDeadband","RegulatingControl.targetValue","ShuntCompensator.aVRDelay","ShuntCompensator.sections"]}
    ,
    "switches": {
        "attribute" : "Switch.open"
     }
    ,

    "regulators" : {
        "attribute" : ["RegulatingControl.targetDeadband","RegulatingControl.targetValue", "TapChanger.initialDelay", "TapChanger.lineDropCompensation","TapChanger.step", "TapChanger.lineDropR","TapChanger.lineDropX"]}

}

class dnp3_mapping():

	
    def on_message(self, headers, message):
        """ Handle incoming messages on the fncs_output_topic for the simulation_id
        Parameters
        ----------
        headers: dict
            A dictionary of headers that could be used to determine topic of origin and
            other attributes.
        message: object
            A data structure following the protocol defined in the message structure
            of ``GridAPPSD``.  Most message payloads will be serialized dictionaries, but that is
            not a requirement.	
	 self._message_count += 1

        # Every message_period messages we are going to turn the capcitors on or off depending
        # on the current capacitor state.
        if self._message_count % message_period == 0:
            if self._last_toggle_on:
                _log.debug("count: {} toggling off".format(self._message_count))
                msg = self._close_diff.get_message()
                self._last_toggle_on = False
            else:
                _log.debug("count: {} toggling on".format(self._message_count))
                msg = self._open_diff.get_message()
                self._last_toggle_on = True

            self._gapps.send(self._publish_to_topic, json.dumps(msg))
   
	    
	    
	    
    def __init__(self,map_file):
	self.c_ao = 0
	self.c_bo = 0
	self.c_ai = 0
	self.c_bi = 0
	with open(map_file, 'r') as f:
            self.file_dict = json.load(f) 
		
	self.out_json= list()

	
    def assign_val(self,data_type,group,variation,index,name,description,measurement_type,measurement_id):
	records = dict()
        records["data_type"] = data_type
        records["index"] = index
        records["group"] = group
        records["variation"] = variation
        records["description"] = description
        records["name"] = name
        records["measurement_type"] = measurement_type
        records["measurement_id"] = measurement_id
        self.out_json.append(records)


    def assign_valc(self,data_type,group,variation,index,name,description,object_id,attribute):
	# for control input points -capacitors, switches,regulators
	records = dict()
	records["data_type"] = data_type
	records["index"] = index
	records["group"] = group
	records["variation"] = variation
	records["description"] = description
	records["name"] = name
	records["object_id"] = object_id
	records["attribute"] = attribute
	self.out_json.append(records)

    def load_json(self,out_json,out_file): 
   	with open(out_file, 'w') as fp:
	    out_dict= dict({'points':out_json})
	    json.dump(out_dict,fp,indent =2, sort_keys=True)

    def _create_dnp3_object_map(self):
	feeders = self.file_dict.get("feeders",[])
	for x in feeders: # reading model.dict json file
	    measurements = x.get("measurements",[])
	    capacitors = x.get("capacitors",[])
	    regulators = x.get("regulators",[])
	    switches = x.get("switches",[])
	    solarpanels = x.get("solarpanels",[])
	    batteries = x.get("batteries",[])

	for m in measurements:
	    measurement_type = m.get("measurementType")
	    measurement_id = m.get("mRID")
	    name =  m.get("name")
	    description = "Equipment is " + m['name'] + "," + m['ConductingEquipment_type'] + " and phase is " + m['phases']
					
	    if m['MeasurementClass'] == "Analog":
		self.assign_val("AO",42,3,self.c_ao,name,description,measurement_type,measurement_id)
		self.c_ao += 1
	    elif m['MeasurementClass'] == "Discrete":
		self.assign_val("BO",11,1,self.c_bo,name,description,measurement_type,measurement_id)
		self.c_bo += 1

	for m in capacitors:
            object_id = m.get("mRID")
    	    name =  m.get("name")
	    phase_value = list(m['phases'])
	    description1 = "Capacitor, " + m['name'] + "," + "phase -" + m['phases']
            cap_attribute = attribute_map['capacitors']['attribute']
	    for l in range(0,4):
		self.assign_valc("AI",32,3,self.c_ai,name,description1,object_id,attribute_map['capacitors']['attribute'][l])
		self.c_ai += 1
	    for j in range(0, len(m['phases'])):
		description = "Capacitor, " + m['name'] + "," + "phase -" + phase_value[j]
		self.assign_valc("BI",2,1,self.c_bi,name,description,object_id,attribute_map['capacitors']['attribute'][4])
		self.c_bi +=1

        for m in solarpanels:
            measurement_id = m.get("mRID")
            name = m.get("name")
            description = "Solarpanel " + m['name'] + "phases - " + m['phases']
            self.assign_val("AI",32,3,self.c_ai,name,description,None,measurement_id)
            self.c_ai +=1

        for m in batteries:
            measurement_id = m.get("mRID")
            name = m.get("name")
            description = "Battery, " + m['name'] + "phases - " + m['phases']
            self.assign_val("AI",32,3,self.c_ai,name,description,None,measurement_id)
            self.c_ai +=1    
            
        for m in switches:
	    object_id = m.get("mRID")
	    name = m.get("name")
	    for k in range(0, len(m['phases'])):
	        phase_value = list(m['phases'])
                description = "Switch, " + m['name'] + "phases - " + phase_value[k]
	  	self.assign_valc("BI",2,1,self.c_bi,name,description,object_id,attribute_map['switches']['attribute'])
	        self.c_bi +=1
			
        for m in regulators:
	    name = m.get("bankName")
	    reg_attribute = attribute_map['regulators']['attribute']
            bank_phase= list(m['bankPhases'])
            description = "Regulator, " + m['bankName'] + " " +"phase is  -  " + m['bankPhases']
	    for n in range(0,5):
	        object_id = m.get("mRID")
		self.assign_valc("AI",32,3,self.c_ai,name,description,object_id[0],reg_attribute[n])
		self.c_ai +=1
            for i in range(4,7):
	        reg_phase_attribute=attribute_map['regulators']['attribute'][i]
	        for j in range(0, len(m['bankPhases'])):
		    description = "Regulator, " + m['tankName'][j] + " " "phase is  -  " + m['bankPhases'][j]
	            object_id = m.get("mRID")
	            self.assign_valc("AI",32,3,self.c_ai,name,description,object_id[j],reg_phase_attribute)
		    self.c_ai +=1

	

	return self.out_json
def _main():
	_log.debug("Starting conversion")
	outfile = dnp3_mapping('model_dict.json')
	a = outfile._create_dnp3_object_map()
	outfile.load_json(a,'points.json')
	
if __name__ == "__main__":
    _main()
