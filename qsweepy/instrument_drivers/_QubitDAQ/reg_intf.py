from numpy import *
##############################
#ADS regs to check program status
ADS_CTRL_ST_ADDR = 0x156
#ADS_CTRL_ST_VL = 0x64
ADS_CTRL_ST_VL = 0xe8
###############################
#Pulse processing module
PULSE_PROC_BASE = 0x0

#Control register
PULSE_PROC_CTRL = 0x0
#Control register bit masks
#++++++++++++++++++++++++++++++++++++
PULSE_PROC_CTRL_START           = 1<<0
PULSE_PROC_CTRL_BUSY            = 1<<1
PULSE_PROC_CTRL_ABORT           = 1<<2
PULSE_PROC_CTRL_EXT_TRIG_EN     = 1<<3
PULSE_PROC_CTRL_RES_DMA_BUSY    = 1<<4
PULSE_PROC_CTRL_RES_DMA_READY   = 1<<5
#++++++++++++++++++++++++++++++++++++

PULSE_PROC_CAP_LEN      = 4
PULSE_PROC_CAP_FIFO_LVL = 8
PULSE_PROC_NSEGM        = 12
PULSE_PROC_CAP_ADDR     = 16
PULSE_PROC_FEATURE_LEN  = 20
PULSE_PROC_RES_DMA_FIFO_LVL  = 24
PULSE_PROC_THRESHOLD    = 28
PULSE_PROC_DOT_AVE      = 72
#############################################
#FX3 usb chip interface module
FX3_BASE = 0x10000

#Control register
FX3_CTRL = 0x0
#Control register bit masks
#++++++++++++++++++++++++++++++++++++
FX3_CTRL_START       = 1<<0   #Read/write process start
FX3_CTRL_WR          = 1<<1   #Direction: 1-write; 0-read
FX3_CTRL_ABORT       = 1<<2   #Read/write process abort
FX3_CTRL_DDR_WR_BUSY = 1<<3   #DDR write status
FX3_CTRL_DDR_RD_BUSY = 1<<4   #DDR read status
FX3_CTRL_RESET       = 1<<5   #Global reset
FX3_CTRL_PATH        = 1<<6   #Data path: 0-DDR3; 1-onchip memory
#++++++++++++++++++++++++++++++++++++

#Other registers
FX3_LEN	            = 4	    #Read/write, data length
FX3_ADDR            = 8 	#Read/write, start address
FX3_CRC32           = 12    #Read/write, CRC32 of FPGA firmware
FX3_FIFO_LVL_DDR_WR = 16    #Read only, DDR write fifo max level
FX3_FIFO_LVL_DDR_RD = 20    #Read only, DDR read fifo max level
##############################################
JESD_BASE = 0x20000
JESD_CTRL  = 0x0

##############################################
RAM_BASE = 0x50000
COV_ST = 0x4
FIFO_ST = 0x5
COV_LEN = 60
COV_THRESH_BASE = 300
COV_THRESH_SUBBASE = 16
COV_RES_BASE = 100
COV_RES_SUBBASE = 16
COV_RESAVG_BASE = 200
COV_RESAVG_SUBBASE = 16
COV_NUMB_BASE = 400

##############################################
#Triggrt source
TRIG_SRC_BASE = 0x60000
TRIG_SRC_CTRL = 0
TRIG_SRC_CTRL_UPDATE = 0 #Set this bit after loading of new values

TRIG_SRC_PERIOD_LO = 4	# 64 bit pulse period in clock cycles
TRIG_SRC_PERIOD_HI =8
TRIG_SRC_WIDTH_LO = 12	# 64 bit pulse width in clock cycles
TRIG_SRC_WIDTH_HI = 16