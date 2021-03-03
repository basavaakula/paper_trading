#!/usr/bin/python3

import sys
from tkinter import Tk, Toplevel, Event, TclError, StringVar, Frame, Menu, \
    Label, Entry, SOLID, RIDGE, N, S, E, W, LEFT, messagebox, IntVar, Scrollbar, RIGHT, BOTTOM, TOP, RIDGE,\
    Listbox, END
from tkinter.ttk import Combobox, Button, Notebook, Checkbutton
from tkinter import ttk
import tkinter as tk
import pandas as pd
import tksheet
import time
from operator import mul, sub, add
import requests
import matplotlib.pyplot as plt
from tkinter.filedialog import askopenfile
from datetime import date
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)

import os.path
from os import path


font = {'family' : 'sans-serif',
        'weight' : 'normal',
        'size'   : 4}

from matplotlib import rc
rc('font', **font)

class OC_DATA():
    def __init__(self)->None:
        self.symb = " "
        self.url_oc = 'https://www.nseindia.com/option-chain'
        self.hdr: Dict[str, str] = {'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                                (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36','accept-language':'en-US,en;q=0.9'}
        self.con_trial = 1
    def set_stock(self,symb):
        self.symb = symb
    
    def get_oc_data(self):
        #self.con_trial = 0
        self.connect_to_nse()
        self.response = self.session.get(self.url,headers=self.hdr,timeout=100,cookies=self.cookies)
        return self.response.json()
    
    def connect_to_nse(self):
        self.con_trial = self.con_trial + 1
        if(self.symb=='NIFTY' or self.symb=='BANKNIFTY'):
            self.url = 'https://www.nseindia.com/api/option-chain-indices?symbol='+self.symb
        else:
            self.url = 'https://www.nseindia.com/api/option-chain-equities?symbol='+self.symb
        try:
            self.session.close()
        except:
            pass
        self.session = requests.Session()
        try:
            request = self.session.get(self.url_oc, headers=self.hdr, timeout=100)
            self.cookies = dict(request.cookies)
        except:
            print("************* reconnecting to NSE *************")
            self.connect_to_nse()
            return
    
    def get_expiry_dates(self):
        #self.con_trial = 0
        self.connect_to_nse()
        self.response = self.session.get(self.url,headers=self.hdr,timeout=100,cookies=self.cookies)
        try:
            json_data = self.response.json()
            self.expiry_dates: List = []
            self.expiry_dates = json_data['records']['expiryDates']
        except:
            self.connect_to_nse()

            
        #print(self.expiry_dates)

class paper_trade:
    def __init__(self, window:Tk)->None:
        self.imp_strikes: List[float] = []
        self.imp_my_buy_price: List[float] = []
        self.nse_adapter = OC_DATA()
        self.stop = False
        self.my_atm: float = 0.0
        self.interval = 10.
        self.first_run = True
        self.buy_pe_limit: List[float] = []
        self.sell_pe_limit: List[float] = []
        self.sell_ce_limit: List[float] = []
        self.buy_ce_limit: List[float] = []
        self.market_price: List[float] = []
        self.vix_percentage = 2
        self.my_buy_price = []
        self.strategies: List[String] = ['IRON CONDOR']
        self.sh_cols: List[List[String]] = [['Instrument','Qty','My_price','LTP','P&L']]
        self.indices: List[str] = ['NIFTY','BANKNIFTY','RELIANCE','ASHOKLEY','TATAMOTORS','SBIN']
        self.indices_lot: dict[str,str]={'NIFTY':'75','BANKNIFTY':'25','RELIANCE':'505','ASHOKLEY':'9000','TATAMOTORS':'5700', \
                                         'SBIN':'3000'}
        self.symb_lot_dict: dict[str,List[str]] = {}
        self.symb_lot_dict['SYMBOLS'] = ['NIFTY','BANKNIFTY','RELIANCE']
        self.symb_lot_dict['LOT_SIZE'] = ['75','25']
        self.setup_main_window(window)
    
    def setup_main_window(self,window)->None:
        self.sh_window: Tk = window
        self.sh_window.title('Paper trading')
        window_width: int = self.sh_window.winfo_reqwidth()
        window_height: int = self.sh_window.winfo_reqheight()
        position_right: int = int(self.sh_window.winfo_screenwidth() / 2 - window_width / 2)
        position_down: int = int(self.sh_window.winfo_screenheight() / 2 - window_height / 2)
        self.sh_window.geometry("1000x800+300+100")
        self.sh_window.grid_rowconfigure(0, weight=0)
        self.sh_window.grid_columnconfigure(0, weight=1)
        rh = self.sh_window.winfo_height()
        rw = self.sh_window.winfo_width()
        #self.sh_window.configure(width=1200,height=800)
        #self.sh_window.grid_propagate(0)
        
        pdx = 5
        pdy = 5
        row_idx = 0
        top_frame: Frame = Frame(self.sh_window,width=rw,height=.1*rh)
        #top_frame.pack(anchor='nw',fill='both', expand=True, side=TOP)
        top_frame.grid(row=0,column=0,sticky='nsew')
        #top_frame.grid_rowconfigure(0, weight=0)
        #top_frame.grid_columnconfigure(0, weight=0)
        #top_frame.grid_propagate(1)
        #top_frame.configure(height=500)
        
        var_stock: StringVar = StringVar()
        var_stock.set(" ")
        lbl_stock: Label = Label(top_frame,text='Symbol',justify=LEFT,font=("TkDefaultFont", 10,"bold"),width=10)
        #lbl_stock.pack(anchor=N, expand=False, side=LEFT)
        lbl_stock.grid(row=0,column=0,sticky='nw',padx=pdx,pady=pdy)
        self.combo_box_stock = Combobox(top_frame,width=10,textvariable=var_stock) 
        #self.combo_box_stock.pack(anchor=N, expand=False, side=LEFT)
        self.combo_box_stock.grid(row=0,column=1,sticky='nw',padx=pdx,pady=pdy)
        self.combo_box_stock.configure(state='readonly')
        self.combo_box_stock['values'] = self.indices
        self.combo_box_stock.bind('<<ComboboxSelected>>', self.set_expiry_date)

        date_var_stock: StringVar = StringVar()
        date_var_stock.set(" ")
        lbl_exp_date_stock: Label = Label(top_frame,text='Expiry',justify=LEFT,font=("TkDefaultFont", 10,"bold"),width=10)
        #lbl_exp_date_stock.pack(anchor=N, expand=False, side=LEFT)
        lbl_exp_date_stock.grid(row=1,column=0,sticky=N+S+W,padx=pdx,pady=pdy)
        self.date_combo_box_stock = Combobox(top_frame,width=10,textvariable=date_var_stock) 
        #self.date_combo_box_stock.pack(anchor=N, expand=False, side=LEFT)
        self.date_combo_box_stock.grid(row=1,column=1,sticky=N+S+W,padx=pdx,pady=pdy)
        self.date_combo_box_stock.configure(state='readonly')
        self.date_combo_box_stock.bind('<<ComboboxSelected>>', self.set_expiry_date)
        #
        var_lot_size: StringVar = StringVar()
        var_lot_size.set(" ")
        lbl_lot_size: Label = Label(top_frame,text='Qty',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        #lbl_lot_size.pack(anchor=N, expand=False, side=LEFT)
        lbl_lot_size.grid(row=0,column=2,sticky=N+S+W,padx=pdx,pady=pdy)
        self.qty_combo_box = Combobox(top_frame,width=10,textvariable=var_lot_size) 
        #self.qty_combo_box.pack(anchor=N, expand=False, side=LEFT)
        self.qty_combo_box.configure(state='readonly')
        self.qty_combo_box.grid(row=0,column=3,sticky=N+S+W,padx=pdx,pady=pdy)
        
        var_vix: StringVar = StringVar()
        var_vix.set(" ")
        lbl_vix: Label = Label(top_frame,text='VIX',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        #lbl_vix.pack(anchor=N, expand=False, side=LEFT)
        lbl_vix.grid(row=1,column=2,sticky=N+S+W,padx=pdx,pady=pdy)
        self.vix_combo_box = Combobox(top_frame,width=10,textvariable=var_vix) 
        #self.vix_combo_box.pack(anchor=N, expand=False, side=LEFT)
        self.vix_combo_box.grid(row=1,column=3,sticky=N+S+W,padx=pdx,pady=pdy)
        self.vix_combo_box.configure(state='readonly')
        self.vix_combo_box['values'] = list(map(lambda x: x/10.0, range(5, 100, 5)))
        self.vix_combo_box.bind('<<ComboboxSelected>>', self.set_VIX)
        

        self.start_button: Button = tk.Button(top_frame,text='Trade',command=self.main_recursive,width=10,bg='green',fg='white',font=("TkDefaultFont", 10, "bold"))
        #self.start_button.pack(anchor=N, expand=False, side=LEFT)
        self.start_button.grid(row=0,column=4,sticky=N+S+W)#,padx=pdx,pady=pdy)
        self.start_button.configure(state='disabled')
        
        self.import_button: Button = tk.Button(top_frame,text='Manual',command=self.import_iron_condor,width=10,bg='red',fg='white',font=("TkDefaultFont", 10, "bold"))
        #self.import_button.pack(anchor=N, expand=False, side=LEFT)
        self.import_button.grid(row=0,column=5,sticky=N+S+W)#,padx=pdx,pady=pdy)
        self.import_button.configure(state='disabled')
        
        self.load_button: Button = tk.Button(top_frame,text='Load trade',command=self.load_file,width=10,bg='yellow',fg='black',font=("TkDefaultFont", 10, "bold"))
        self.load_button.grid(row=1,column=4,sticky=N+S+W+E)
        self.load_button.configure(state='normal')
        
        self.lbl_nse_con_time: Label = Label(top_frame,text=' ',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        #self.lbl_nse_con_time.pack(anchor=N, expand=False, side=LEFT)
        self.lbl_nse_con_time.grid(row=0,column=6,sticky=N+S+W+E)
        
        bot_frame: Frame = Frame(self.sh_window,width=1200,height=.3*rh)
        #bot_frame.pack(anchor='nw', fill='both',expand=True, side=TOP)
        bot_frame.grid(row=1,column=0,sticky='nsew')
        #bot_frame.grid_rowconfigure(0, weight=1)
        #bot_frame.grid_columnconfigure(0, weight=1)
        #bot_frame.grid_propagate(0)
        
        self.plot_frame: Frame = Frame(self.sh_window,width=1200, height=.6*rh)
        #self.plot_frame.pack(anchor='nw', fill='both',expand=True, side=TOP)
        self.plot_frame.grid(row=2,column=0,sticky="nsew")
        #self.plot_frame.grid_rowconfigure(0, weight=1)
        #self.plot_frame.grid_columnconfigure(0, weight=1)
        #self.plot_frame.grid_propagate(0)
        
        fig = Figure(figsize = (2, 2), dpi = 200) 
        self.plot1 = fig.add_subplot(111)
        self.plot1.tick_params(axis='both', which='minor', labelsize=8)

        self.canvas = FigureCanvasTkAgg(fig,master = self.plot_frame)
        self.canvas.get_tk_widget().pack(anchor=N,fill='both',expand=True) 
        
        self.NB: Notebook = Notebook(bot_frame)
        self.NB.pack(anchor=N,fill="both", expand=True)
        self.NBF: List[Frame] = []
        self.NBS: List[tksheet.Sheet] = []
        self.NB_DF: List[pd.Dataframe] = []
        
        for strat in enumerate(self.strategies):
            self.NBF.append(Frame(self.NB))
            self.NB.add(self.NBF[-1],text=strat[1])
            sh = tksheet.Sheet(self.NBF[-1], column_width=100, align="center",
                                                  headers = self.sh_cols[strat[0]],
                                                  header_font=("TkDefaultFont", 10, "bold"),
                                                  empty_horizontal=0, empty_vertical=20, header_height=35)
            sh.enable_bindings(
            ("toggle_select", "drag_select", "column_select", "row_select", "column_width_resize",
             "arrowkeys", "right_click_popup_menu", "rc_select", "copy", "select_all"))
            sh.pack(anchor=W,fill="both", expand=True)
            #sh.change_theme("dark")
            self.NBS.append(sh)
    
    def export_iron_condor(self):
        self.imp_strikes.clear()
        self.imp_my_buy_price.clear()
        for i in enumerate(self.imp_cbox):
            if(i[1].get()==""):
                break
            self.imp_strikes.append(float(i[1].get()))
            self.imp_my_buy_price.append(float(self.imp_tbox[i[0]].get('1.0',END)))
        df_export: pd.DataFrame = pd.DataFrame()
        df_export['Strikes'] = self.imp_strikes
        df_export['Buy_price'] = self.imp_my_buy_price
        save_name = self.combo_box_stock.get()+'-'+self.date_combo_box_stock.get()+'-'+datetime.now().strftime("%H:%M:%S")
        df_export.to_csv(save_name+'.csv')
        
        self.imp_wd.destroy() 
        self.import_button.configure(state='disabled')
    
    def save_current_data(self):
        save_name = self.combo_box_stock.get()+'_'+self.date_combo_box_stock.get()+'_'+date.today().strftime("%b-%d-%Y")+'.csv'
        if(not path.exists(save_name)):
            df_export: pd.DataFrame = pd.DataFrame()
            df_export['Strikes'] = self.df['Instrument']
            df_export['Buy_price'] = self.df['My_price']
            df_export['Qty'] = [(self.df['Qty'].tolist())[0]]*5
            df_export.to_csv(save_name)

    def load_file(self): 
        file = askopenfile(mode ='r', filetypes =[('CSV files', '*.csv')]) 
        self.df_loaded: pd.DataFrame = pd.read_csv(file.name)
        self.imp_strikes = self.df_loaded['Strikes'].tolist()
        self.imp_my_buy_price = self.df_loaded['Buy_price'].tolist()
        qty = (self.df_loaded['Qty'].tolist())[0]
        name_split = (os.path.basename(file.name)).split('_')
        print(name_split)
        self.combo_box_stock.set(name_split[0])
        self.date_combo_box_stock.set(name_split[1])
        self.qty_combo_box.set(qty)
        self.nse_adapter.set_stock(self.combo_box_stock.get())
        self.main_recursive()
    
    def open_file(self): 
        file = askopenfile(mode ='r', filetypes =[('CSV files', '*.csv')]) 
        #if file is not None: 
        #    content = file.read() 
        #    print(content) 
        self.df_loaded: pd.DataFrame = pd.read_csv(file.name)
        self.imp_strikes = self.df_loaded['Strikes'].tolist()
        self.imp_my_buy_price = self.df_loaded['Buy_price'].tolist()
        self.imp_wd.destroy() 
        self.import_button.configure(state='disabled')
    
    def import_iron_condor(self):
        self.imp_wd: Tk = Tk()
        self.imp_wd.title('Paper trading')
        window_width: int = self.imp_wd.winfo_reqwidth()
        window_height: int = self.imp_wd.winfo_reqheight()
        position_right: int = int(self.imp_wd.winfo_screenwidth() / 2 - window_width / 2)
        position_down: int = int(self.imp_wd.winfo_screenheight() / 2 - window_height / 2)
        self.imp_wd.geometry("600x300+300+200")
        
        bot_frame: Frame = Frame(self.imp_wd,width=800, height=300)
        bot_frame.pack(anchor='nw', fill='both',expand=True, side=TOP)
        bot_frame.pack_propagate(0)
        
        json_data = self.nse_adapter.get_oc_data()
        match_date = self.date_combo_box_stock.get()
        strike_prices: List[float] = [data['strikePrice'] for data in json_data['records']['data'] \
                                   if (str(data['expiryDate']).lower() == str(match_date).lower())]
        

        self.imp_cbox: List[Combobox]    = []
        self.imp_tbox: List[tk.Text]    = []
        imp_vars: List[StringVar] = []
        imp_lbls: List[Label]     = []
        imp_lbls_txt: List[Label] = ['buy PUT','sell PUT','sell CALL','buy CALL']
        imp_lbls_color: List[Label] = ['green','red','red','green']
            
        row_idx = 0

        for i in enumerate(imp_lbls_txt):
            str_var = StringVar()
            str_var.set(' ')
            lbl: Label = Label(bot_frame,text=i[1],justify=LEFT,font=("TkDefaultFont", 10,"bold"),fg=imp_lbls_color[i[0]],width=20)
            lbl.grid(row=i[0],column=0,sticky=N+S+W)
            cb = Combobox(bot_frame,width=10,textvariable=str_var) 
            cb.grid(row=i[0],column=1,sticky=N+S+W)
            cb.configure(state='readonly')
            cb['values'] = strike_prices
            self.imp_cbox.append(cb)
            txt = tk.Text(bot_frame,width=10,bg='yellow',height=2)
            txt.grid(row=i[0],column=2,sticky=N+S+W)
            self.imp_tbox.append(txt)
            row_idx = i[0]+1
        
        ok_button: Button = tk.Button(bot_frame,text='OK!',command=self.export_iron_condor,width=20,bg='green',fg='white',font=("TkDefaultFont", 10, "bold"))
        ok_button.grid(row=row_idx,column=4,sticky=N+S+W)
        
        load_button: Button = tk.Button(bot_frame,text='Load',command=self.open_file,width=20,bg='green',fg='white',font=("TkDefaultFont", 10, "bold"))
        load_button.grid(row=row_idx+1,column=4,sticky=N+S+W)

        
    def set_VIX(self,event):
        self.vix_percentage = float(self.vix_combo_box.get())
    def set_expiry_date(self,event):
        self.nse_adapter.set_stock(self.combo_box_stock.get())
        self.nse_adapter.get_expiry_dates()
        self.date_combo_box_stock['values'] = tuple(self.nse_adapter.expiry_dates)
        self.date_combo_box_stock.set(self.nse_adapter.expiry_dates[0])
        qtys = [x*int(self.indices_lot[self.combo_box_stock.get()]) for x in range(1,11)]
        self.qty_combo_box['values'] = qtys
        self.qty_combo_box.set(qtys[0])
        self.start_button.configure(state='normal')
        self.import_button.configure(state='normal')
    
    def main_recursive(self)->None:
        if(self.first_run):
            self.start_button.configure(state='disabled')
            self.combo_box_stock.configure(state='disabled')
            self.date_combo_box_stock.configure(state='disabled')
            self.qty_combo_box.configure(state='disabled')
            self.refresh_data()
            self.first_run = False
        self.curr_time = time.time()
        time_passed = int(self.curr_time-self.prev_time)
        if(time_passed>=self.interval):
            self.refresh_data()
        else:
            self.sh_window.after((10 * 1000),self.main_recursive)
            return
        if(not self.stop):
            self.sh_window.after((10 * 1000),self.main_recursive)
            return

    def refresh_data(self):
        for strat in enumerate(self.strategies):
            curr_sh = self.NBS[strat[0]]
            if(strat[1]=='IRON CONDOR'):
                df = self.df_iron_condor()
                for col in enumerate(df.columns):
                    curr_sh.set_column_data(col[0],values=df[col[1]])
                for i in range(curr_sh.get_total_rows()):
                    if(float(curr_sh.get_cell_data(i,len(df.columns)-1))<=0.0):
                        curr_sh.highlight_cells(row=i, column=len(df.columns)-1, bg='white',fg='red')
                    if(float(curr_sh.get_cell_data(i,len(df.columns)-1))>0.0):
                        curr_sh.highlight_cells(row=i, column=len(df.columns)-1, bg='green',fg='white')
        self.prev_time = time.time()
        curr_sh.refresh()

    
    def df_iron_condor(self):
        df: pd.DataFrame = pd.DataFrame()
        df_graph: pd.DataFrame = pd.DataFrame()
        
        buy_pe_pl: List[float] = []
        sell_pe_pl: List[float] = []
        sell_ce_pl: List[float] = []
        buy_ce_pl: List[float] = []
        
        start = time.time()
        json_data = self.nse_adapter.get_oc_data()
        end = time.time();
        strr = "NSE response time (sec) : " + str(round(end-start,2)) + " ( " + str(self.nse_adapter.con_trial) + " hits)"
        self.lbl_nse_con_time.config(text=strr)
        match_date = self.date_combo_box_stock.get()
        print(match_date)
        strike_prices: List[float] = [data['strikePrice'] for data in json_data['records']['data'] \
                                   if (str(data['expiryDate']).lower() == str(match_date).lower())]
        ce_values: List[dict] = [data['CE'] for data in json_data['records']['data'] \
                    if "CE" in data and (str(data['expiryDate'].lower()) == str(match_date.lower()))]
        pe_values: List[dict] = [data['PE'] for data in json_data['records']['data'] \
                    if "PE" in data and (str(data['expiryDate'].lower()) == str(match_date.lower()))]
         
        ce_data: pd.DataFrame = pd.DataFrame(ce_values)
        pe_data: pd.DataFrame = pd.DataFrame(pe_values)
       
        #print(list(ce_data.columns))
        
        pe_otm_data: pd.DataFrame = pd.DataFrame()
        ce_otm_data: pd.DataFrame = pd.DataFrame()

        df_call_buy: pd.DataFrame = pd.DataFrame() 

        strike_diff: List[float] = []
        
        
        curr_price = ce_data['underlyingValue'][0]
        self.sh_window.title('Paper trading-->'+self.combo_box_stock.get()+' ('+str(curr_price)+' ) last updated @--'+datetime.now().strftime("%H:%M:%S"))
        if(self.first_run):
            diff = [abs(x-curr_price) for x in strike_prices]
            min_pos = diff.index(min(diff))
            self.my_atm = strike_prices[min_pos]
            
        strike_diff = list(map(lambda x:x-self.my_atm,strike_prices))
        
        iron_condor_strikes: List[float] = []
        if(len(self.imp_strikes)==0):
            search_strike = (1-(self.vix_percentage/100.))*self.my_atm
            diff = [abs(x-search_strike) for x in strike_prices]
            min_pos = diff.index(min(diff))
            sell_pe_idx = min_pos

            buy_pe_idx = sell_pe_idx-1
            iron_condor_strikes.append(buy_pe_idx)#buy_pe_strike
            iron_condor_strikes.append(sell_pe_idx)#sell_pe_strike
         
            pe_otm_data = pe_data.iloc[iron_condor_strikes] 
            
            iron_condor_strikes.clear()
            search_strike = (1+(self.vix_percentage/100.))*self.my_atm
            diff = [abs(x-search_strike) for x in strike_prices]
            min_pos = diff.index(min(diff))
            sell_ce_idx = min_pos
            iron_condor_strikes.append(min_pos)#sell_ce_strike
            
            buy_ce_idx = sell_ce_idx + 1
            iron_condor_strikes.append(buy_ce_idx)#buy_ce_strike
            
            ce_otm_data = ce_data.iloc[iron_condor_strikes]
        else:
            iron_condor_strikes.append(strike_prices.index(self.imp_strikes[0]))
            iron_condor_strikes.append(strike_prices.index(self.imp_strikes[1]))
            pe_otm_data = pe_data.iloc[iron_condor_strikes] 
            buy_pe_idx = iron_condor_strikes[0]
            sell_pe_idx = iron_condor_strikes[1]
            
            iron_condor_strikes.clear()
            iron_condor_strikes.append(strike_prices.index(self.imp_strikes[2]))
            iron_condor_strikes.append(strike_prices.index(self.imp_strikes[3]))
            ce_otm_data = ce_data.iloc[iron_condor_strikes]
            
            sell_ce_idx = iron_condor_strikes[0]
            buy_ce_idx = iron_condor_strikes[1]
            
            self.my_buy_price = self.imp_my_buy_price
            

        
        pd_concat = pd.concat([pe_otm_data,ce_otm_data],axis=0)
        sell_buy_signs = [1.,-1.,-1.,1.]
        lot_list = [float(self.qty_combo_box.get())]*4
        qty_list = list(map(mul,lot_list,sell_buy_signs))
        ltp_list = list(map(float,pd_concat['lastPrice'].tolist()))
        if(self.first_run and len(self.imp_strikes)==0):
            self.my_buy_price = pd_concat['lastPrice'].tolist()
        
        net_points: List[float] = list(map(mul,sell_buy_signs,self.my_buy_price))
        net_points = list(map(lambda x: x*-1,net_points))
        tt = list(map(sub,ltp_list,self.my_buy_price))
        df['Instrument'] = pd_concat['strikePrice'].tolist() 
        df['Qty'] = qty_list
        df['My_price'] = list(map(float,self.my_buy_price))
        df['LTP'] = ltp_list
        df['P&L'] = list(map(mul,tt,qty_list))
        df['P&L'] =  df['P&L'].round(3)
        total_row = {'Instrument':' ','Qty':' ','My_price':str(round(sum(net_points),2)),'LTP':'Total ','P&L':df['P&L'].sum()}
        df = df.append(total_row,ignore_index=True)
        
        for i in range(len(strike_prices)):
            if(i>=buy_pe_idx):
                val = -self.my_buy_price[0]
            else:
                val = abs(strike_prices[i]-strike_prices[buy_pe_idx])-self.my_buy_price[0]
            buy_pe_pl.append(val)
            
            if(i>=sell_pe_idx):
                val = self.my_buy_price[1]
            else:
                val = self.my_buy_price[1]-abs(strike_prices[i]-strike_prices[sell_pe_idx])
            sell_pe_pl.append(val)
            
            if(i<=sell_ce_idx):
                val = self.my_buy_price[2]
            else:
                val = self.my_buy_price[2]-abs(strike_prices[i]-strike_prices[sell_ce_idx])
            sell_ce_pl.append(val)
            
            if(i<=buy_ce_idx):
                val = -self.my_buy_price[3]
            else:
                val = abs(strike_prices[i]-strike_prices[buy_ce_idx])-self.my_buy_price[3]
            buy_ce_pl.append(val)
        
        self.buy_pe_limit.append((pd_concat['strikePrice'].tolist())[0])
        self.sell_pe_limit.append((pd_concat['strikePrice'].tolist())[1])
        self.sell_ce_limit.append((pd_concat['strikePrice'].tolist())[2])
        self.buy_ce_limit.append((pd_concat['strikePrice'].tolist())[3])
        self.market_price.append(curr_price)
        
        ttl1 = list(map(add,buy_pe_pl,sell_pe_pl)) 
        ttl2 = list(map(add,buy_ce_pl,sell_ce_pl)) 
        ttl3 = list(map(add,ttl1,ttl2)) 
        ttl3 = list(map(lambda x:x*float(self.qty_combo_box.get()),ttl3))
        df_graph['sell_call'] = ttl3

        #plt.clf()
        #plt.plot(strike_prices,ttl3,'-b')
        #plt.axvline(x=(pd_concat['strikePrice'].tolist())[0],linestyle='--',color='g')
        #plt.axvline(x=(pd_concat['strikePrice'].tolist())[1],linestyle='--',color='r')
        #plt.axvline(x=(pd_concat['strikePrice'].tolist())[2],linestyle='--',color='r')
        #plt.axvline(x=(pd_concat['strikePrice'].tolist())[3],linestyle='--',color='g')
        #plt.plot(curr_price,df['P&L'].iloc[0:-1].sum(),'D')
        #plt.text(1.05*min(strike_prices),.9*max(ttl3),'max_profit = '+str(round(max(ttl3),2)),color='green',fontsize='10')
        #plt.text(1.05*min(strike_prices),.3*max(ttl3),'max_loss = '+str(round(min(ttl3),2)),color='red',fontsize='10')
        #clr = 'red'
        #if(df['P&L'].iloc[0:-1].sum()>0):
        #    clr = 'green'
        #plt.text(1.01*curr_price,1.01*df['P&L'].iloc[0:-1].sum(),str(df['P&L'].iloc[0:-1].sum()),color=clr,fontsize='8')
        #plt.pause(.0001)
        #plt.show(block = False)
        #plt.title('Paper trading-->'+self.combo_box_stock.get()+' ('+str(curr_price)+' ) last updated @--'+datetime.now().strftime("%H:%M:%S"))
        self.strike_prices = strike_prices
        self.pd_concat = pd_concat
        self.curr_price = curr_price
        self.ttl3 = ttl3
        self.df = df
        self.draw_plot()
        self.save_current_data()
        return df
        
    def draw_plot(self):
        self.plot1.clear()
        self.plot1.plot(self.strike_prices,self.ttl3,'-b',lw=.8)
        self.plot1.axvline(x=(self.pd_concat['strikePrice'].tolist())[0],linestyle='--',color='g',lw=.8)
        self.plot1.axvline(x=(self.pd_concat['strikePrice'].tolist())[1],linestyle='--',color='r',lw=.8)
        self.plot1.axvline(x=(self.pd_concat['strikePrice'].tolist())[2],linestyle='--',color='r',lw=.8)
        self.plot1.axvline(x=(self.pd_concat['strikePrice'].tolist())[3],linestyle='--',color='g',lw=.8)
        self.plot1.plot(self.curr_price,self.df['P&L'].iloc[0:-1].sum(),'D',markersize=2)
        self.plot1.text(1.01*min(self.strike_prices),.5*max(self.ttl3),'max_profit ='+str(round(max(self.ttl3),2)),color='green',fontsize='6')
        self.plot1.text(1.1*min(self.strike_prices),.5*max(self.ttl3),'max_loss = '+str(round(min(self.ttl3),2)),color='red',fontsize='6')
        clr = 'red'
        if(self.df['P&L'].iloc[0:-1].sum()>0):
            clr = 'green'
        self.plot1.text(1.01*self.curr_price,1.01*self.df['P&L'].iloc[0:-1].sum(),str(self.df['P&L'].iloc[0:-1].sum()),color=clr,fontsize='4')
        self.canvas.draw()
        
if __name__ == '__main__':
    master_window: Tk = Tk()
    paper_trade(master_window)
    master_window.mainloop()
