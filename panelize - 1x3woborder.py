from kikit import panelize_ui_impl as ki
from kikit.units import mm, deg
from kikit.panelize import Panel, BasicGridPosition, Origin
from pcbnewTransition.pcbnew import LoadBoard, VECTOR2I
from pcbnewTransition import pcbnew
from itertools import chain
import os


############### Custom config
board1_path = "..\\uPLC-Analog\\CAD\\uplc-analog\\uplc-analog.kicad_pcb"
board2_path = "..\\uPLC-Digital\\CAD\\uplc-digital\\uplc-digital.kicad_pcb"
board3_path = "..\\uPLC-Relay\\CAD\\uplc\\uplc.kicad_pcb"
output_path = ".\\CAD\\Panel\\uPLC-Panel.kicad_pcb"


#make the folder if it does not exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)

board_spacing = 2*mm

################ KiKit Panel Config (Only deviations from default)

#framing={
#		"type": "none", #only rail on top and bottom
#		"vspace" : "2mm", # space between board and rail
#		"width": "7.5mm" # Width of the rail
#	}
	
cuts =  {
		"type": "mousebites",
		"drill": "0.5mm",
  		"spacing": "0.75mm",
    	"offset": "0.1mm",
     	"prolong": "0.5mm"
	}
tabs = { #Add tabs between board and board as well as board and rail
		"type":"fixed", #Place them with constant width and spacing
  		"vcount": 2,
#   	"hcount": 2,
		"vwidth": "2.7mm",
	}

#fiducials = {
#     "type":"3fid",
#     "hoffset": "6mm",
#     "voffset": "6mm",
#     "coppersize": "1mm",
#     "opening": "2mm"
#}

#copperfill = {
#	"type": "hatched",
#	"width": "0.5mm",
# 	"clearance": "2mm"
#}

#text = {
#    "type":"simple",
#    "text": "\nuPLC-FullStack - {date}",
#   	"anchor": "ml",
#	"vjustify":"top",
#	"voffset ": "5000mm",
# 	"hoffset ": "5000mm",
#    "orientation": "90deg"
#}


#tooling = {
#        "type": "3hole",
#        "hoffset": "3mm",
#        "voffset": "3mm",
#        "size": "3mm"
#    }

post={
	"millradius": "1mm"
}

# Obtain full config by combining above with default
preset = ki.obtainPreset([], tabs=tabs, cuts=cuts, post=post)


################ Adjusted `panelize_ui#doPanelization`

# Prepare			
board1 = LoadBoard(board1_path)
board2 = LoadBoard(board2_path)
board3 = LoadBoard(board3_path)
panel = Panel(output_path)


panel.inheritDesignSettings(board1)
panel.inheritProperties(board1)
panel.inheritTitleBlock(board1)




###### Manually build layout. Inspired by `panelize_ui_impl#buildLayout`
sourceArea1 = ki.readSourceArea(preset["source"], board1)
sourceArea2 = ki.readSourceArea(preset["source"], board2)
sourceArea3 = ki.readSourceArea(preset["source"], board3)
substrateCount = len(panel.substrates) # Store number of previous boards (probably 0)
# Prepare renaming nets and references
netRenamer = lambda x, y: "{orig}.{n}".format(n=x, orig=y)
refRenamer = lambda x, y: "{orig}.{n}".format(n=x, orig=y)


# Actually place the individual boards
# Use existing grid positioner
# Place two boards above each other
panelOrigin = VECTOR2I(0,0)
placer = BasicGridPosition(board_spacing, board_spacing) #HorSpace, VerSpace
area1 = panel.appendBoard(board1_path, panelOrigin + placer.position(0,0, None) ,rotationAngle=180*deg, origin=Origin.Center, sourceArea=sourceArea1, netRenamer=netRenamer, refRenamer=refRenamer)
area2 = panel.appendBoard(board2_path, panelOrigin + placer.position(1,0, area1),rotationAngle=180*deg, origin=Origin.Center, sourceArea=sourceArea2, netRenamer=netRenamer, refRenamer=refRenamer,  inheritDrc=False)
area3 = panel.appendBoard(board3_path, panelOrigin + placer.position(2,0, area2),rotationAngle=180*deg, origin=Origin.Center, sourceArea=sourceArea3, netRenamer=netRenamer, refRenamer=refRenamer,  inheritDrc=False)

substrates = panel.substrates[substrateCount:] # Collect set of newly added boards

# Prepare frame and partition
framingSubstrates = ki.dummyFramingSubstrate(substrates, preset)
panel.buildPartitionLineFromBB(framingSubstrates)
backboneCuts = ki.buildBackBone(preset["layout"], panel, substrates, preset)


######## --------------------- Continue doPanelization

tabCuts = ki.buildTabs(preset, panel, substrates, framingSubstrates)

frameCuts = ki.buildFraming(preset, panel)


ki.buildTooling(preset, panel)
ki.buildFiducials(preset, panel)
for textSection in ["text", "text2", "text3", "text4"]:
	ki.buildText(preset[textSection], panel)
ki.buildPostprocessing(preset["post"], panel)

ki.makeTabCuts(preset, panel, tabCuts)
ki.makeOtherCuts(preset, panel, chain(backboneCuts, frameCuts))


ki.buildCopperfill(preset["copperfill"], panel)

ki.setStackup(preset["source"], panel)
ki.setPageSize(preset["page"], panel, board1)
ki.positionPanel(preset["page"], panel)

ki.runUserScript(preset["post"], panel)

ki.buildDebugAnnotation(preset["debug"], panel)

panel.save(reconstructArcs=preset["post"]["reconstructarcs"],
		   refillAllZones=preset["post"]["refillzones"])