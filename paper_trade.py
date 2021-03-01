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
from operator import mul, sub

sys.path.append('/home/abasava/GIT/option_fetcher')
import OC_DATA


class paper_trade:
    def __init__(self, window:Tk)->None:
        self.nse_adapter = OC_DATA.OC_DATA()
        self.stop = False
        self.my_atm: float = 0.0
        self.interval = 10.
        self.first_run = True
        self.vix_percentage = 4
        self.my_buy_price = []
        self.strategies: List[String] = ['IRON CONDOR']
        self.sh_cols: List[List[String]] = [['Instrument','Qty','My_price','LTP','P&L']]
        self.indices: List[str] = ['NIFTY','BANKNIFTY']
        self.indices_lot: dict[str,str] = {'NIFTY':'75','BANKNIFTY':'25'}
        self.setup_main_window(window)
    
    def setup_main_window(self,window)->None:
        self.sh_window: Tk = window
        self.sh_window.title('Paper trading')
        window_width: int = self.sh_window.winfo_reqwidth()
        window_height: int = self.sh_window.winfo_reqheight()
        position_right: int = int(self.sh_window.winfo_screenwidth() / 2 - window_width / 2)
        position_down: int = int(self.sh_window.winfo_screenheight() / 2 - window_height / 2)
        self.sh_window.geometry("1200x600+300+200")


        top_frame: Frame = Frame(self.sh_window,width=1200, height=100)
        top_frame.pack(anchor='nw',fill='x', expand=False, side=TOP)
        
        var_stock: StringVar = StringVar()
        var_stock.set(" ")
        lbl_stock: Label = Label(top_frame,text='Symbol',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        lbl_stock.pack(anchor=N, expand=False, side=LEFT)
        self.combo_box_stock = Combobox(top_frame,width=10,textvariable=var_stock) 
        self.combo_box_stock.pack(anchor=N, expand=False, side=LEFT)
        self.combo_box_stock.configure(state='readonly')
        self.combo_box_stock['values'] = self.indices
        self.combo_box_stock.bind('<<ComboboxSelected>>', self.set_expiry_date)

        date_var_stock: StringVar = StringVar()
        date_var_stock.set(" ")
        lbl_exp_date_stock: Label = Label(top_frame,text='Expiry',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        lbl_exp_date_stock.pack(anchor=N, expand=False, side=LEFT)
        self.date_combo_box_stock = Combobox(top_frame,width=10,textvariable=date_var_stock) 
        self.date_combo_box_stock.pack(anchor=N, expand=False, side=LEFT)
        self.date_combo_box_stock.configure(state='readonly')
        self.date_combo_box_stock.bind('<<ComboboxSelected>>', self.set_expiry_date)
        
        var_lot_size: StringVar = StringVar()
        var_lot_size.set(" ")
        lbl_lot_size: Label = Label(top_frame,text='Qty',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        lbl_lot_size.pack(anchor=N, expand=False, side=LEFT)
        self.qty_combo_box = Combobox(top_frame,width=10,textvariable=var_lot_size) 
        self.qty_combo_box.pack(anchor=N, expand=False, side=LEFT)
        self.qty_combo_box.configure(state='readonly')
        

        self.start_button: Button = tk.Button(top_frame,text='*** Execute ***',command=self.main_recursive,width=20,bg='green',fg='white',font=("TkDefaultFont", 10, "bold"))
        self.start_button.pack(anchor=N, expand=False, side=LEFT)
        self.start_button.configure(state='disabled')
        
        self.lbl_nse_con_time: Label = Label(top_frame,text=' ',justify=LEFT,font=("TkDefaultFont", 10, "bold"))
        self.lbl_nse_con_time.pack(anchor=N, expand=False, side=LEFT)
        
        bot_frame: Frame = Frame(self.sh_window,width=1200, height=400)
        bot_frame.pack(anchor='nw', fill='both',expand=True, side=TOP)
        
        self.NB: Notebook = Notebook(bot_frame)
        self.NB.pack(anchor=N,fill="both", expand=True)
        self.NBF: List[Frame] = []
        self.NBS: List[tksheet.Sheet] = []
        self.NB_DF: List[pd.Dataframe] = []
        
        for strat in enumerate(self.strategies):
            self.NBF.append(Frame(self.NB))
            self.NB.add(self.NBF[-1],text=strat[1])
            sh = tksheet.Sheet(self.NBF[-1], column_width=200, align="center",
                                                  headers = self.sh_cols[strat[0]],
                                                  header_font=("TkDefaultFont", 10, "bold"),
                                                  empty_horizontal=0, empty_vertical=20, header_height=35)
            sh.enable_bindings(
            ("toggle_select", "drag_select", "column_select", "row_select", "column_width_resize",
             "arrowkeys", "right_click_popup_menu", "rc_select", "copy", "select_all"))
            sh.pack(anchor=W,fill="both", expand=True)
            self.NBS.append(sh)

    def set_expiry_date(self,event):
        self.nse_adapter.set_stock(self.combo_box_stock.get())
        self.nse_adapter.get_expiry_dates()
        self.date_combo_box_stock['values'] = tuple(self.nse_adapter.expiry_dates)
        self.date_combo_box_stock.set(self.nse_adapter.expiry_dates[0])
        qtys = [x*int(self.indices_lot[self.combo_box_stock.get()]) for x in range(1,11)]
        self.qty_combo_box['values'] = qtys
        self.qty_combo_box.set(qtys[0])
        self.start_button.configure(state='normal')
    
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
        self.prev_time = time.time()
        curr_sh.refresh()

    
    def df_iron_condor(self):
        df: pd.DataFrame = pd.DataFrame()
        start = time.time()
        json_data = self.nse_adapter.get_oc_data()
        end = time.time();
        strr = "NSE response time (sec) : " + str(round(end-start,2)) + " ( " + str(self.nse_adapter.con_trial) + " hits)"
        self.lbl_nse_con_time.config(text=strr)
        match_date = self.date_combo_box_stock.get()
        strike_prices: List[float] = [data['strikePrice'] for data in json_data['records']['data'] \
                                   if (str(data['expiryDate']).lower() == str(match_date).lower())]
        ce_values: List[dict] = [data['CE'] for data in json_data['records']['data'] \
                    if "CE" in data and (str(data['expiryDate'].lower()) == str(match_date.lower()))]
        pe_values: List[dict] = [data['PE'] for data in json_data['records']['data'] \
                    if "PE" in data and (str(data['expiryDate'].lower()) == str(match_date.lower()))]
         
        ce_data: pd.DataFrame = pd.DataFrame(ce_values)
        pe_data: pd.DataFrame = pd.DataFrame(pe_values)
        
        pe_otm_data: pd.DataFrame = pd.DataFrame()
        ce_otm_data: pd.DataFrame = pd.DataFrame()

        
        if(self.first_run):
            curr_price = ce_data['underlyingValue'][0]
            diff = [abs(x-curr_price) for x in strike_prices]
            min_pos = diff.index(min(diff))
            self.my_atm = strike_prices[min_pos]
            
        iron_condor_strikes: List[float] = []
        search_strike = (1-(self.vix_percentage/100.))*self.my_atm
        diff = [abs(x-search_strike) for x in strike_prices]
        min_pos = diff.index(min(diff))
        iron_condor_strikes.append(min_pos)#sell_pe_strike

        search_strike = (1-((self.vix_percentage+.5)/100.))*self.my_atm#adding 0.5% for the buy hedge positions
        diff = [abs(x-search_strike) for x in strike_prices]
        min_pos = diff.index(min(diff))
        iron_condor_strikes.append(min_pos)#buy_pe_strike
     
        pe_otm_data = pe_data.iloc[iron_condor_strikes] 
        iron_condor_strikes.clear()
        
        search_strike = (1+(self.vix_percentage/100.))*self.my_atm
        diff = [abs(x-search_strike) for x in strike_prices]
        min_pos = diff.index(min(diff))
        iron_condor_strikes.append(min_pos)#sell_ce_strike
        
        search_strike = (1+((self.vix_percentage+.5)/100.))*self.my_atm#adding 0.5% for the buy hedge positions
        diff = [abs(x-search_strike) for x in strike_prices]
        min_pos = diff.index(min(diff))
        iron_condor_strikes.append(min_pos)#buy_ce_strike
        
        ce_otm_data = ce_data.iloc[iron_condor_strikes]

        
        pd_concat = pd.concat([pe_otm_data,ce_otm_data],axis=0)
        pd_concat = pd.concat([pe_otm_data,ce_otm_data],axis=0)
        sell_buy_signs = [1.,-1.,-1.,1.]
        lot_list = [float(self.qty_combo_box.get())]*4
        qty_list = list(map(mul,lot_list,sell_buy_signs))
        ltp_list = list(map(float,pd_concat['lastPrice'].tolist()))
        if(self.first_run):
            self.my_buy_price = pd_concat['lastPrice'].tolist()
        
        tt = list(map(sub,ltp_list,self.my_buy_price))
        #df['Instrument'] = pd_concat['identifier'].tolist() 
        df['Instrument'] = pd_concat['strikePrice'].tolist() 
        df['Qty'] = qty_list
        df['LTP'] = ltp_list
        df['My_price'] = list(map(float,self.my_buy_price))
        df['P&L'] = list(map(mul,tt,qty_list))
        
        return df
        

if __name__ == '__main__':
    master_window: Tk = Tk()
    paper_trade(master_window)
    master_window.mainloop()
