victron_protocol = Proto("victron", "Victron precision shunt")
local gatt = Dissector.get("btatt")
local btatt_value_f = Field.new("btatt.value")
local btatt_handle_f = Field.new("btatt.handle")
local btatt_opcode_f = Field.new("btatt.opcode")

fields = victron_protocol.fields 

fields.status   = ProtoField.uint8("victron.status", "Status", base.HEX)
fields.transaction_id = ProtoField.uint8 ("victron.transaction_id", "TransactionId", base.HEX)
fields.remaining   = ProtoField.uint8("victron.remaining", "Remainig pkts", base.DEC)
fields.protocol_type   = ProtoField.uint8("victron.protocol_type", "prot type", base.HEX)

local value_types = {
	[0x8c] = "Current",
	[0x8d] = "Voltage",
	[0x8e] = "Power",
	--[0x8f] = "Capacity",
	[0x7d] = "Starter",
	
}
local command_categories = {
	[0x03190308] = "history values",
	[0x03190309] = "history bools",
	[0x10190308] = "settings values",
	[0x10190309] = "settings bools",
	[0x03] = "unknown",
	[0xed190308] = "values values",
	[0xed190309] = "values bools",
	[0x0f190308] = "mixed settings",
}

local data_types = {
	[0x08] = "value (has length)",
	[0x09] = "bool (1byte fixed len)",
}

fields.state_of_charge = ProtoField.float("victron.state_of_charge", "Battery Charge Status", {" %"}, base.DEC or base.UNIT_STRING)
fields.bool_bat_start_sync = ProtoField.bool("victron.bat_start_sync", "battery starts synchronized")
local mixed_settings = {
	[0xfd] = fields.bool_bat_start_sync,
	[0xff] = fields.state_of_charge,
}

fields.command_category = ProtoField.uint32("victron.cmd_category", "command category", base.HEX, command_categories)
fields.start_sequence   = ProtoField.uint32("victron.start_sequence", "start_squence", base.HEX)
fields.data_type   = ProtoField.uint8("victron.data_type", "data type", base.HEX, data_types)
fields.value   = ProtoField.uint8("victron.command", "command", base.HEX, value_types)
local settings_types = {
	[0x00] = "set capacity!",
	[0x01] = "set charged voltage!",
	[0x02] = "set tail current!",
	[0x03] = "set charged detection time!",
	[0x04] = "set charge eff. factor!",
	[0x05] = "set peukert coefficient!",
	[0x06] = "set current threshold",
	[0x07] = "set time-to-go avg. per.",
	[0x08] = "set discharge floor!",
	[0xff] = "Battery Charge Status", -- this should go into a separate table for category mixed_settings
}
fields.settings_value   = ProtoField.uint8("victron.settings", "settings", base.HEX, settings_types)

local hist_types = {
	[0x00] = "hist: deepest discharge",
	[0x01] = "hist: last discharge",
	[0x02] = "hist: Average Discharge",
	[0x03] = "hist: total charge cycles",
	[0x04] = "hist: full discharges",
	[0x05] = "hist: Cumulative Ah drawn",
	[0x06] = "hist: Min battery voltage",
	[0x07] = "hist: Max battery voltage",
	[0x08] = "hist: Time since last full",
	[0x09] = "hist: synchronizations",
	[0x10] = "hist: Discharged Energy",
	[0x11] = "hist: Charged Energy",
	
}
fields.history = ProtoField.uint8("victron.history", "history", base.HEX, hist_types)
fields.hist_synch = ProtoField.uint16("victron.hist_synch", hist_types[0x09], base.DEC)
fields.hist_cycles = ProtoField.uint16("victron.cycles", hist_types[0x03], base.DEC)
fields.hist_deepest_discharge = ProtoField.float("victron.hist_deepest_discharge", hist_types[0x00], {" Ah"}, base.UNIT_STRING)
fields.hist_last_discharge = ProtoField.float("victron.hist_last_discharge", hist_types[0x01], {" Ah"}, base.UNIT_STRING)
fields.hist_avrg_discharge = ProtoField.float("victron.hist_avrg_discharge", hist_types[0x02], {" Ah"}, base.UNIT_STRING)
fields.hist_full_discharge = ProtoField.uint16("victron.hist_full_discharge", hist_types[0x04], base.DEC)
fields.hist_cum_drawn = ProtoField.float("victron.cum_drawn", hist_types[0x05], {" Ah"}, base.UNIT_STRING)
fields.hist_min_bat = ProtoField.float("victron.hist_min_bat", hist_types[0x06], {" V"}, base.UNIT_STRING)
fields.hist_max_bat = ProtoField.float("victron.hist_max_bat", hist_types[0x07], {" V"}, base.UNIT_STRING)
fields.hist_time_full = ProtoField.int32("victron.hist_time_full", hist_types[0x08])
fields.hist_discharged_energy = ProtoField.float("victron.hist_discharged_energy",  hist_types[0x10], {" kWh"}, base.UNIT_STRING)
fields.hist_charged_energy = ProtoField.float("victron.hist_charged_energy",  hist_types[0x11], {" kWh"}, base.UNIT_STRING)


fields.settings_value   = ProtoField.uint8("victron.settings", "settings", base.HEX, settings_types)


command_class_type = { [0x0] = "status reply?", [0x4] ="data reply?", [0x8] = "bulk values??"}
fields.command_class   = ProtoField.uint8("victron.command_class", "command class", base.HEX, command_class_type)

data_size_type = { [0x08] = "8byte", [0x04] = "4ybte" , [0x02]="2byte", [0x01] = "1byte"}
fields.data_size   = ProtoField.uint8("victron.data_size", "data size", base.DEC)

fields.payload   = ProtoField.bytes("victron.payload", "payload", base.SPACE)
fields.data   = ProtoField.bytes("victron.data", "data", base.SPACE)
fields.arguments   = ProtoField.bytes("victron.arguments", "arguments", base.SPACE)
fields.crc   = ProtoField.uint8("victron.crc", "crc", base.HEX)
fields.reserved   = ProtoField.uint8("victron.reserved", "Reserved", base.HEX)


fields.voltage   = ProtoField.uint16("victron.voltage", "voltage", base.HEX)
fields.current   = ProtoField.int32("victron.current", "current", base.DEC)
fields.power   = ProtoField.int16("victron.power", "power", base.DEC)
fields.starter   = ProtoField.int16("victron.starter", "starter", base.DEC)
--fields.capacity   = ProtoField.float("victron.capacity", "capacity (%)", base.UNIT_STRING, { [0]="%"})
fields.capacity   = ProtoField.int32("victron.capacity", "capacity (Ah)")
fields.set_capacity   = ProtoField.int32("victron.set_capacity", "set capacity (Ah)")

fields.set_charged_volt  = ProtoField.float("victron.charged_voltage", "charged Voltage ", {" V"})
fields.set_dis_floor  = ProtoField.uint16("victron.dis_floor", "discharge floor ", base.UNIT_STRING, {" %"})
fields.set_tail_current  = ProtoField.float("victron.set_tail_current", "set tail current ", {" %"})
fields.set_peukert  = ProtoField.float("victron.set_peukert", "set peukert coeff", {"%"})
fields.set_curr_threshold= ProtoField.float("victron.set_curr_threshold", "set current threshold (A)", {[1]=" A"})

fields.set_charged_time= ProtoField.uint16("victron.set_charged_time", "set charged det. time ", base.UNIT_STRING,{" min"})
fields.set_eff_factor  = ProtoField.uint16("victron.set_eff_factor", "charge eff. factor ",base.UNIT_STRING or base.DEC ,{" %"})
fields.set_timetogo  = ProtoField.uint16("victron.timetogo", "time-to-go avg. period", base.UNIT_STRING,{" min"})
fields.set_booltype  = ProtoField.uint8("victron.set_booltype", "bool type", base.HEX)
fields.set_boolvalue  = ProtoField.bool("victron.set_boolvalue", "bool value")


fields.unknown8   = ProtoField.uint8("victron.unknown8", "Unknown8 value", base.HEX)
fields.unknown16   = ProtoField.uint16("victron.unknown16", "Unknown16 value", base.HEX)
fields.unknown24   = ProtoField.uint24("victron.unknown24", "Unknown24 value", base.HEX)
fields.unknown32   = ProtoField.uint32("victron.unknown32", "Unknown32 value", base.HEX)
fields.unknown_bool_type  = ProtoField.uint8("victron.unknown_bool_type", "unknwon bool type", base.HEX)
fields.unknown_bool_value  = ProtoField.bool("victron.unknown_bool_value", "unknown bool value")

local statuses = {
[0x00] = "New Command",
[0x01] = "Command Busy",
[0x02] = "Command Successful",
[0x03] = "Command Failure",
[0x04] = "Command No Response / Command Timeout",
[0x05] = "Command Not Support",
[0x82] = "Status Result",
}



function payload_dissector(buffer, pinfo, tree, size, command)
	fun = (command_dissector[command] and command_dissector[command]) or default_command
	fun(buffer,pinfo,tree,size,command)
end

fields.device_id   = ProtoField.uint64("victron.device_id", "device_id?", base.HEX)
local packet_types = {[0x0027] = "Bulk Values", [0x0024] = "Single Value"}
fields.packet_type = ProtoField.uint16("victron.packet_type", "packet type", base.HEX, packet_types)
local direction = { [0x52] = "send", [0x1b] = "recv", [0x001b] = "recv"}
fields.command_dir   = ProtoField.uint8("victron.command_dir", "direction", base.HEX, direction, 0xff)


function length_one(buffer, pinfo, subtree)
		
	-- pinfo.cols.info = name
	subtree:add_le(fields.reserved, buffer(0,1))

end



function voltage(buffer,pinfo,subtree)
	local val = buffer(0,2):le_uint() / 100
	subtree:add_le(fields.voltage, buffer(0,2)):append_text(": "..val.."V")
	pinfo.cols.info = "voltage: " .. val
	return 2
end

function current(buffer,pinfo,subtree)
	local val = buffer(0,4):le_int() /1000
	subtree:add_le(fields.current, buffer(0,4), val, "current"):append_text(": "..val.."A")
	pinfo.cols.info = "current: " .. val .."A"
	return 4
end

function power(buffer,pinfo,subtree)
	local val = buffer(0,2):le_int() 
	subtree:add_le(fields.power, buffer(0,2)):append_text(": "..val.."W")
	pinfo.cols.info = "power: " .. val .."W"
	return 2
end

function starter(buffer,pinfo,subtree)
	local val = buffer(0,2):le_int() /100
	subtree:add_le(fields.starter, buffer(0,2), val):append_text(": "..val.."V")
	pinfo.cols.info = "starter: " .. val .. "V"
	return 2
end

-- function capacity(buffer,pinfo,subtree, text)
-- 	local val =  buffer(0,2):le_uint() 
-- 	local capa = val / 0xFFFF *100
-- 	subtree:add(fields.capacity, buffer(0,2), val )
-- 	pinfo.cols.info = text..": " .. val 
-- 	return 2
-- end

function set_capacity(buffer,pinfo,subtree)
	local val =  buffer(0,2):le_uint() 
	subtree:add(fields.set_capacity, buffer(0,2), val )
	pinfo.cols.info = "set capacity: " .. val 
	return 2
end

function set_avg_period(buffer,pinfo,subtree)
	subtree:add(fields.set_timetogo, buffer(0,2):le_uint())
	pinfo.cols.info = "set time-to-go:" ..buffer(0,2):le_uint()
	return 2
end

function set_dis_floor(buffer,pinfo,subtree)
	subtree:add(fields.set_dis_floor, buffer(0,2):le_uint()/10)
	pinfo.cols.info = "set discharge floor:" ..buffer(0,2):le_uint()/10
	return 2
end


function set_charged_time(buffer,pinfo,subtree)
	subtree:add(fields.set_charged_time, buffer(0,2):le_uint())
	pinfo.cols.info = "set charged det. time:" ..buffer(0,2):le_uint()
	return 2
end

function set_charged_volt(buffer,pinfo,subtree)
	local  val = buffer(0,2):le_uint()/10.0
	subtree:add(fields.set_charged_volt, buffer(0,2),val)
	pinfo.cols.info = "set charged volt:" ..val
	return 2
end

function set_eff_factor(buffer,pinfo,subtree)
	local  val = buffer(0,2):le_uint()
	subtree:add(fields.set_eff_factor,buffer(0,2), val)
	pinfo.cols.info = "set charge eff. factor" ..val
	return 2
end

function set_tail_current(buffer,pinfo,subtree)
	local  val = buffer(0,2):le_uint() /10.0
	subtree:add(fields.set_tail_current,buffer(0,2), val)
	pinfo.cols.info = "set tail current" ..val
	return 2
end

function set_peukert(buffer,pinfo,subtree)
	local  val = buffer(0,2):le_uint() /100
	subtree:add(fields.set_peukert,buffer(0,2), val)
	pinfo.cols.info = "set peukert coeff" ..val
	return 2
end

function set_curr_threshold(buffer,pinfo,subtree)
	local  val = buffer(0,2):le_uint() /100
	subtree:add(fields.set_curr_threshold,buffer(0,2), val)
	pinfo.cols.info = "set current threshold" ..val
	return 2
end

function add_unknown_bool(buffer,pinfo,subtree)

	subtree:add_le(fields.unknown_bool_type, buffer(0,1))
	subtree:add_le(fields.unknown_bool_value, buffer(1,1))
	return 2
end

function add_unknown_field(buffer,pinfo,subtree)
		-- unknwond filed depending on data size
	if data_size_nibble == 1 then
		unknown_field = fields.unknown8
	end

	if data_size_nibble == 2 then
		unknown_field = fields.unknown16
	end
	if data_size_nibble == 3 then
		unknown_field = fields.unknown24
	end
	if data_size_nibble == 4 then
		unknown_field = fields.unknown32
	end

		subtree:add_le(unknown_field, buffer(0,data_size_nibble))
		return data_size_nibble
end

local value_types_functions = {
	[0x8c] = current,
	[0x8d] = voltage,
	[0x8e] = power,
	--[0x8f] = "Capacity",
	[0x7d] = starter,
	
}

function command_category(buffer, pinfo, subtree)
	command_type = buffer(0,1):le_uint() 
	command_fun = value_types_functions[command_type]
	if command_fun == nil then
		command_fun = add_unknown_field
	end

	return command_fun(buffer(2),pinfo,subtree)
end


function settings_bool(buffer, pinfo, subtree)
	subtree:add_le(fields.set_booltype, buffer(0,1))
	subtree:add_le(fields.set_boolvalue, buffer(1,1))
	return 2
end

function settings_category(buffer, pinfo,subtree)
 local type_funcs = {
		[0x00] = set_capacity,
		[0x01] = set_charged_volt,
		[0x02] = set_tail_current,
		[0x03] = set_charged_time,
		[0x04] = set_eff_factor,
		[0x05] = set_peukert,
		[0x06] = set_curr_threshold,
		[0x07] = set_avg_period,
		[0x08] = set_dis_floor,
		
		
	}
	settings_type = buffer(0,1):le_uint() 
	fun = type_funcs[settings_type]
	if fun == nil then
		fun = add_unknown_field
	end
	
	return fun(buffer(2),pinfo,subtree)
end

function mixed_settings(buffer, pinfo, subtree)
	local type = buffer(4,1):le_uint()

	if type == 0xff then
		local val = buffer(6,2):le_uint() / 100
		subtree:add_le(fields.state_of_charge, buffer(6,2), val)
		return 2
	end

	local bool_field = mixed_settings[type] or fields.unknown_bool_type
	subtree:add_le(bool_field, buffer(6,1))
	return 1
end

function hist_category(buffer, pinfo,subtree, data_size)
	local hist_commands = {
		[0x00] = {fields.hist_deepest_discharge,10},
		[0x01] = {fields.hist_last_discharge,10},
		[0x02] = {fields.hist_avrg_discharge,10},
		[0x03] = {fields.hist_cycles,1},
		[0x04] = {fields.hist_full_discharge,1},
		[0x05] = {fields.hist_cum_drawn,10},
		[0x06] = {fields.hist_min_bat,100},
		[0x07] = {fields.hist_max_bat,100},
		[0x08] = {fields.hist_time_full,1},
		[0x09] = {fields.hist_synch,1},
		[0x10] = {fields.hist_discharged_energy,100},
		[0x11] = {fields.hist_charged_energy,100},
	 }
	 command = buffer(0,1):le_uint() 
	 fun = hist_commands[command][1]
	 if fun == nil then
		 fun = fields.unknown32
	 end
	 local value = buffer(2,data_size):le_int() / hist_commands[command][2] 
	 subtree:add_le(fun, buffer(2,data_size), value)
	 return data_size
 end

function single_value(buffer,pinfo,subtree)	
	if buffer:len() <6 then
		return 0
	end
	subtree:add_le(fields.start_sequence, buffer(0,4))
	local data_type = buffer(0,1):le_uint()
	subtree:add_le(fields.data_type, buffer(0,1), data_type)

	local category = buffer(0,4):le_uint()
	subtree:add_le(fields.command_category, buffer(3,1), category)

	command_class_nibble = bit.rshift( bit.band(buffer(5,1):uint() , 0xf0) ,4)
	subtree:add_le(fields.command_class, buffer(5,1), command_class_nibble)
	data_size_nibble = bit.band(buffer(5,1):uint() , 0x0f)
	subtree:add_le(fields.data_size , buffer(5,1), data_size_nibble)
	local consumed = 6

	print("buffer:"..buffer(0,4):le_uint())
	if buffer(0,4):le_uint() == 0x10190308 then
		subtree:add_le(fields.settings_value, buffer(4,1))
		return consumed + settings_category(buffer(4), pinfo, subtree)
	end

	if buffer(0,4):le_uint() == 0x10190309 then
		subtree:add_le(fields.settings_value, buffer(4,1))
		return consumed + settings_bool(buffer(4), pinfo, subtree)
	end

	if buffer(0,4):le_uint() == 0xed190308 then
		subtree:add_le(fields.value, buffer(4,1))
		return consumed + command_category(buffer(4), pinfo, subtree)
	end
	

	if buffer(0,4):le_uint() == 0x03190308 then
		subtree:add_le(fields.history, buffer(4,1))
		return consumed + hist_category(buffer(4), pinfo, subtree, data_size_nibble)
	end
	
	if buffer(0,4):le_uint() == 0x0f190308 then
		subtree:add_le(fields.settings_value, buffer(4,1))
		return mixed_settings(buffer,pinfo,subtree)
	end
	
	
	if  data_type== 0x09 then
		return add_unknown_bool(buffer(4),pinfo,subtree)
	else
		return add_unknown_field(buffer(6),pinfo,subtree)
	end
end



function bulkvalues(buffer,pinfo,tree)	
	local packet_type = buffer(1,2):le_uint()
	local data_start =  buffer(3)
	tvbs = {}

	print("data_Types:"..buffer(0,4):le_uint())
	if command_categories[buffer(0,1):le_uint()] == nil then
		print("header unknwon, need more bytes")
		pinfo.desegment_offset = 5
		pinfo.desegment_len = DESEGMENT_ONE_MORE_SEGMENT
		return 0
	end

	-- get the length of the packet buffer (Tvb).
	local pktlen = buffer:len()
	local bytes_consumed = 0
	

	while bytes_consumed < pktlen do
		local subtree = tree:add(victron_protocol, "Bulk Value", buffer)
		local result = single_value(buffer(bytes_consumed), pinfo, subtree)
		if result == 0 then
			print("need more bytes")
			pinfo.desegment_offset = 5
			pinfo.desegment_len = DESEGMENT_ONE_MORE_SEGMENT
			print("set pinfo desegment_offset "..pinfo.desegment_offset or "nil")
			print("set pinfo.desegment_len "..pinfo.desegment_len)
	
			return pktlen
		end
		print("consumed:"..result)
		bytes_consumed = bytes_consumed + result
	end

	return bytes_consumed
end


function sending(buffer, pinfo, subtree)
	local send_commands = {
		[0xf941] = "Ping",
		[0xf980] = "0xf980",
	}	
	--subtree:add(fields.data, buffer(0))--:append_text(" ("..send_commands[buffer(3,2):uint()]..")")
	
end

function victron_protocol.dissector(buffer, pinfo, tree)
	gatt:call(buffer, pinfo, tree)
	local opcode = btatt_opcode_f().value
	local packet_type = btatt_handle_f().value
	local btatt_value = btatt_value_f()

	--works but creates new data window
	buffer = btatt_value.value:tvb()

	local length = buffer:len()
	if length <= 3 then
		return
	end

	pinfo.cols.protocol = victron_protocol.name

	-- first 3 byte are handled by btatt dissector
	-- subtree:add_le(fields.command_dir, buffer(0,1)):append_text("send CMD")
	-- subtree:add_le(fields.characteristic, buffer(1,2))
	--local packet_type = buffer(1,2):le_uint()
	
	--subtree:add_le(fields.data, buffer(0))--hilft nix mehr, bei BT_ATT gucken
	--subtree:add_le(fields.reserved, buffer(3,4))
	
	local subtree = tree:add(victron_protocol, buffer)
	subtree:add_le(fields.packet_type, packet_type):set_generated()
	
	print("start pinfo desegment_offset "..pinfo.desegment_offset or "nil")
	print("start pinfo.desegment_len "..pinfo.desegment_len)
	

	if opcode == 0x52 then
		sending(buffer, pinfo, subtree)
		return
	end
	print("buffer length:"..length)
	local bytes_consumed = 0
	if packet_type == 0x0027 then
		bytes_consumed = bulkvalues(buffer,pinfo,subtree)
	else	
		bytes_consumed = single_value(buffer,pinfo,subtree)
	end
	print("end bytes cons"..bytes_consumed)
	print("end pinfo desegment_offset "..pinfo.desegment_offset)
	print("end pinfo.desegment_len "..pinfo.desegment_len)
	return bytes_consumed 
end
DissectorTable.get("btl2cap.cid"):add(0x0004, victron_protocol)