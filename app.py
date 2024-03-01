from flask import Flask, render_template, request , redirect
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import base64
import logging
import math
from lightweight_charts import Chart


app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)

def calculate_adx(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    plus_dm = (high - high.shift(1)).clip(lower=0)
    minus_dm = (low.shift(1) - low).clip(lower=0)
    
    atr = tr.ewm(span=window, min_periods=window).mean()
    plus_dm_smooth = plus_dm.ewm(span=window, min_periods=window).mean()
    minus_dm_smooth = minus_dm.ewm(span=window, min_periods=window).mean()

    plus_di = (plus_dm_smooth / atr) * 100
    minus_di = (minus_dm_smooth / atr) * 100

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100

    adx = dx.ewm(span=window, min_periods=2).mean()
    
    return adx

def calculate_atr(df, period=14):
    df['TR'] = df.apply(lambda row: max(row['High'] - row['Low'],
                                        abs(row['High'] - row['Close'].shift(1)),
                                        abs(row['Low'] - row['Close'].shift(1))), axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df['ATR']

def calculate_sma(df, window=20):
    return df['Close'].rolling(window=window).mean()


@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/best' , methods=['POST'] )
def plot_best():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        df = pd.read_csv(io.StringIO(file.stream.read().decode("UTF8")))
        df.index = pd.to_datetime(df.index)
        #window = int(request.form['window'])
        adx = calculate_adx(df.High, df.Low, df.Close)

        # fig, ax = plt.subplots(1, 1, sharex=True, figsize=(18, 10))
        # mpf.plot(df, type='candle', style='charles', ax=ax)
        chart = Chart()
        data = df
        data = data.rename(columns={'High' : 'high' , 'Low' : 'low' , 'Close' : 'close' , 'Open' : 'open' , 'Timestamp (UTC)' : 'time'})
        chart.set(data)

        i = 14
        j = 14
        ct = 0
        longest_length = 0
        longest_line_data = None

        while(i < len(adx) and j < len(adx)):
            if adx[j] < 26:
                j = j + 1
            elif ct <= 1 or ct <= (j-i)/10:
                ct = ct + 1
                j = j + 1
            else:
                a = df.High[i:j+1]
                b = df.Low[i:j+1]
                
                # if j - i <= 10:
                #     ct = 0
                #     i = j
                #     continue
                if ct == 0:
                    hi = a.nlargest(1).iloc[-1]  
                    lo = b.nsmallest(1).iloc[-1]
                    line_length = j - i
                    if line_length > longest_length:
                        longest_length = line_length
                        longest_line_data = (lo, hi, i, j)
                elif len(a) >= ct and len(b) >= ct:
                    hi = a.nlargest(ct).iloc[-1]  
                    lo = b.nsmallest(ct).iloc[-1]
                    line_length = j - i
                    if line_length > longest_length:
                        longest_length = line_length
                        longest_line_data = (lo, hi, i, j)
                ct = 0
                i = j

        if longest_line_data:
            lo, hi, i, j = longest_line_data
            # ax.axhline(y=lo, color='b', linestyle='-', xmin=i / len(df), xmax=j / len(df))
            # ax.axhline(y=hi, color='r', linestyle='-', xmin=i / len(df), xmax=j / len(df))
            # ax.text(0.01 , 0.95 , f"Longest range: {longest_length} Candles" , transform=ax.transAxes , fontsize=12 , verticalalignment='top')
            # ax.text(0.01 , 0.90 , f"Width: {hi-lo}" , transform=ax.transAxes , fontsize=12 , verticalalignment='top')
            chart.trend_line(start_time=data.time[i] , end_time=data.time[j] , start_value=hi , end_value=hi , color='red')
            chart.trend_line(start_time=data.time[i] , end_time=data.time[j] , start_value=lo , end_value=lo , color='blue')
        # buffer = io.BytesIO()
        # plt.savefig(buffer, format='png')
        # buffer.seek(0)
        # plot_data = base64.b64encode(buffer.getvalue()).decode()

        # plt.close(fig)

        # return '<img src="data:image/png;base64,{}">'.format(plot_data)
        chart.show()
    return redirect('/')    

@app.route('/plot', methods=['POST'])
def plot():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        df = pd.read_csv(io.StringIO(file.stream.read().decode("UTF8")))
        df.index = pd.to_datetime(df.index)
        window = float(request.form['window_size'])
        tick = float(request.form['tick_size'])
        chart = Chart()
        data = df
        data = data.rename(columns={'High' : 'high' , 'Low' : 'low' , 'Close' : 'close' , 'Open' : 'open' , 'Timestamp (UTC)' : 'time'})
        chart.set(data)
        

        # fig, ax = plt.subplots(1, 1, sharex=True, figsize=(18, 10))
        # mpf.plot(df, type='candle', style='charles', ax=ax)

        # longest_length = 0
        # longest_line_data = None
        # ul = df.High.max()+1
        # ll = df.Low.min()-1
        # inc = tick
        # itr = int((ul-ll)/inc)+1

        # for k in range(itr):
        #     lr = float(ll + k*inc)
        #     ur = float(lr+window)
        #     i = 0
        #     j = 0
        #     ct = 0

        #     while(i<len(df.Close) and j<len(df.Close)):
        #         if df.High[j] - tick <= ur and df.Low[j] + tick >= lr:
        #             j = j+1
        #         elif ct <= 2 or ct <= (j-i)/10:
        #             ct = ct + 1
        #             j = j + 1
        #         else:
                    
        #             line_length = j - i
        #             if line_length > longest_length:
        #                 longest_length = line_length
        #                 longest_line_data = (lr , ur , i , j)
    
        #             ct = 0
        #             i = j

        # while(i < len(df.Close) and j < len(df.Close)):
        #     if l == 0:
        #         if df.High[j] - df.Low[j] - 2*tick <= window:
        #             j = j+1
        #             l = l+1
        #         elif ct < 2 or ct < (j-i)/10:
        #             ct = ct+1
        #             j = j+1


        # if longest_line_data:
        #     lr , ur , i , j = longest_line_data
        #     ax.axhline(y=lr, color='b', linestyle='-', xmin=i / len(df), xmax=j / len(df))
        #     ax.axhline(y=ur, color='r', linestyle='-', xmin=i / len(df), xmax=j / len(df))
        #     ax.text(0.01 , 0.95 , f"Longest range: {longest_length} Candles" , transform=ax.transAxes , fontsize=12 , verticalalignment='top')

        adx = calculate_adx(df.High, df.Low, df.Close)

        i = 14
        j = 14
        ct = 0
        sum = 0
        n = 0
        while(i < len(adx) and j < len(adx)):
            if adx[j] < 26 and df.High[j] - df.Low[j] - 2*tick <= window:
                j = j + 1
            elif ct <= 2 or ct <= (j-i)/10:
                ct = ct + 1
                j = j + 1
            else:
                a = df.High[i:j+1]
                b = df.Low[i:j+1]
                x = a.mean()
                y = b.mean()
                # if j - i <= 10:
                #     ct = 0
                #     i = j
                #     continue
                if ct == 0:
                    hi = a.mean()
                    lo = b.mean()
                    mid = (x+y)/2
                    app.logger.debug(mid)
                    line_length = j - i
                    if line_length <= 2:
                        ct = 0
                        i = j
                        continue
                    #ax.axhline(y=mid-window/2, color='b', linestyle='-', xmin=i / len(df), xmax=j / len(df))
                    #ax.axhline(y=mid+window/2, color='r', linestyle='-', xmin=i / len(df), xmax=j / len(df))
                    chart.trend_line(start_time=data.time[i] , end_time=data.time[j] , start_value=mid + window/2 , end_value=mid + window/2 , color='red')
                    chart.trend_line(start_time=data.time[i] , end_time=data.time[j] , start_value=mid - window/2 , end_value=mid - window/2 , color='blue')
                    n = n+1
                    n = n+1
                    sum = sum + line_length
                elif len(a) >= ct and len(b) >= ct:
                    hi = a.max()
                    lo = b.min()
                    mid = (x+y)/2
                    line_length = j - i
                    if line_length <= 2:
                        ct = 0
                        i = j
                        continue
                    #ax.axhline(y=mid-window/2, color='b', linestyle='-', xmin=i / len(df), xmax=j / len(df))
                    #ax.axhline(y=mid+window/2, color='r', linestyle='-', xmin=i / len(df), xmax=j / len(df)) 
                    chart.trend_line(start_time=data.time[i] , end_time=data.time[j] , start_value=mid + window/2 , end_value=mid + window/2 , color='red')
                    chart.trend_line(start_time=data.time[i] , end_time=data.time[j] , start_value=mid - window/2 , end_value=mid - window/2 , color='blue')
                    n = n+1
                    sum = sum + line_length             
                ct = 0
                i = j
        if n:
            chart.topbar.textbox('Average' , initial_text=f'Average : {math.floor(sum/n)} candles')
        else:
            chart.topbar.textbox(initial_text='No range found')

        chart.show(block=True)
        # if n:
        #     ax.text(0.01 , 0.95 , f"Average range: {math.floor(sum/n)} Candles" , transform=ax.transAxes , fontsize=12 , verticalalignment='top') 
        # else:
        #     ax.text(0.01 , 0.95 , f"No range found" , transform=ax.transAxes , fontsize=12 , verticalalignment='top') 
        #buffer = io.BytesIO()
        #plt.savefig(buffer, format='png')
        #buffer.seek(0)
        #plot_data = base64.b64encode(buffer.getvalue()).decode()

        #plt.close(fig)

        #return '<img src="data:image/png;base64,{}">'.format(plot_data)
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
