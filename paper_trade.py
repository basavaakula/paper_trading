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

#sys.path.append('/home/abasava/GIT/option_fetcher')
#import OC_DATA

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
        self.url = 'https://www.nseindia.com/api/option-chain-indices?symbol='+self.symb
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
        
        self.import_button: Button = tk.Button(top_frame,text='*** IMPORT ***',command=self.import_iron_condor,width=20,bg='red',fg='white',font=("TkDefaultFont", 10, "bold"))
        self.import_button.pack(anchor=N, expand=False, side=LEFT)
        self.import_button.configure(state='disabled')
        
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
        self.imp_wd.destroy() 
        self.import_button.configure(state='disabled')
    def import_iron_condor(self):
        self.imp_wd: Tk = Tk()
        #self.imp_wd.mainloop()
        self.imp_wd.title('Paper trading')
        window_width: int = self.imp_wd.winfo_reqwidth()
        window_height: int = self.imp_wd.winfo_reqheight()
        position_right: int = int(self.imp_wd.winfo_screenwidth() / 2 - window_width / 2)
        position_down: int = int(self.imp_wd.winfo_screenheight() / 2 - window_height / 2)
        self.imp_wd.geometry("600x300+300+200")
        
        bot_frame: Frame = Frame(self.imp_wd,width=800, height=300)
        bot_frame.pack(anchor='nw', fill='both',expand=True, side=TOP)
        
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

        df_call_buy: pd.DataFrame = pd.DataFrame() 

        strike_diff: List[float] = []
        
        
        curr_price = ce_data['underlyingValue'][0]
        self.sh_window.title('Paper trading-->'+self.combo_box_stock.get()+'--'+self.date_combo_box_stock.get()+'--'+str(curr_price))
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
            sell_pe_idx = iron_condor_strikes[0]
            
            iron_condor_strikes.clear()
            iron_condor_strikes.append(strike_prices.index(self.imp_strikes[2]))
            iron_condor_strikes.append(strike_prices.index(self.imp_strikes[3]))
            ce_otm_data = ce_data.iloc[iron_condor_strikes]
            
            sell_ce_idx = iron_condor_strikes[0]
            buy_ce_idx = iron_condor_strikes[1]
            
            self.my_buy_price = self.imp_my_buy_price
            

        
        pd_concat = pd.concat([pe_otm_data,ce_otm_data],axis=0)
        #pd_concat = pd.concat([pe_otm_data,ce_otm_data],axis=0)
        sell_buy_signs = [1.,-1.,-1.,1.]
        lot_list = [float(self.qty_combo_box.get())]*4
        qty_list = list(map(mul,lot_list,sell_buy_signs))
        ltp_list = list(map(float,pd_concat['lastPrice'].tolist()))
        if(self.first_run and len(self.imp_strikes)==0):
            self.my_buy_price = pd_concat['lastPrice'].tolist()
        
        tt = list(map(sub,ltp_list,self.my_buy_price))
        #df['Instrument'] = pd_concat['identifier'].tolist() 
        df['Instrument'] = pd_concat['strikePrice'].tolist() 
        df['Qty'] = qty_list
        df['My_price'] = list(map(float,self.my_buy_price))
        df['LTP'] = ltp_list
        df['P&L'] = list(map(mul,tt,qty_list))
        df['P&L'] =  df['P&L'].round(3)
        total_row = {'Instrument':' ','Qty':' ','My_price':' ','LTP':'Total ','P&L':df['P&L'].sum()}
        df = df.append(total_row,ignore_index=True)
        
        for i in range(len(strike_prices)):
            if(i>buy_pe_idx):
                val = -self.my_buy_price[0]
            else:
                val = -self.my_buy_price[0]+strike_diff[i]
            buy_pe_pl.append(val)
            
            if(i>sell_pe_idx):
                val = self.my_buy_price[1]
            else:
                val = self.my_buy_price[1]+strike_diff[i]
            sell_pe_pl.append(val)
            
            if(i<=sell_ce_idx):
                val = self.my_buy_price[2]
            else:
                val = self.my_buy_price[2]+strike_diff[i]
            sell_ce_pl.append(val)
            
            if(i<=buy_ce_idx):
                val = -self.my_buy_price[3]
            else:
                val = -self.my_buy_price[3]+strike_diff[i]
            buy_ce_pl.append(val)
        
        self.buy_pe_limit.append((pd_concat['strikePrice'].tolist())[0])
        self.sell_pe_limit.append((pd_concat['strikePrice'].tolist())[1])
        self.sell_ce_limit.append((pd_concat['strikePrice'].tolist())[2])
        self.buy_ce_limit.append((pd_concat['strikePrice'].tolist())[3])
        self.market_price.append(curr_price)
        
        ttl1 = list(map(add,buy_pe_pl,sell_pe_pl)) 
        ttl2 = list(map(add,sell_ce_pl,buy_ce_pl)) 
        ttl3 = list(map(add,ttl1,ttl2)) 
        df_graph['sell_call'] = ttl3
        #plt.plot(strike_prices,ttl3,'-')
        
        #plt.clf()
        ##x_data = range(len(self.buy_pe_limit))
        ##plt.xlim([0,1.1*len(x_data)])
        ##plt.plot(x_data,self.buy_pe_limit,'-g')
        ##plt.plot(x_data,self.sell_pe_limit,'-r')
        ##plt.plot(x_data,self.sell_ce_limit,'-r')
        ##plt.plot(x_data,self.buy_ce_limit,'-g')
        ##plt.plot(x_data,self.market_price,'--b')
        #plt.plot(strike_prices,buy_ce_pl,'--b')
        #plt.pause(.0001)
        #plt.show(block = False)
        return df
        

if __name__ == '__main__':
    master_window: Tk = Tk()
    paper_trade(master_window)
    master_window.mainloop()
