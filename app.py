from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import base64

app = Flask(__name__)

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

        fig, ax = plt.subplots(1, 1, sharex=True, figsize=(18, 10))
        mpf.plot(df, type='candle', style='charles', ax=ax)

        i = 14
        j = 14
        ct = 2
        longest_length = 0
        longest_line_data = None

        while(i < len(adx) and j < len(adx)):
            if adx[j] < 26:
                j = j + 1
            elif ct <= 2 or ct <= (j-i)/10:
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
            ax.axhline(y=lo, color='b', linestyle='-', xmin=i / len(df), xmax=j / len(df))
            ax.axhline(y=hi, color='r', linestyle='-', xmin=i / len(df), xmax=j / len(df))
            ax.text(0.01 , 0.95 , f"Longest range: {longest_length} Candles" , transform=ax.transAxes , fontsize=12 , verticalalignment='top')
            ax.text(0.01 , 0.90 , f"Width: {hi-lo}" , transform=ax.transAxes , fontsize=12 , verticalalignment='top')
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()

        plt.close(fig)

        return '<img src="data:image/png;base64,{}">'.format(plot_data)    

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

        fig, ax = plt.subplots(1, 1, sharex=True, figsize=(18, 10))
        mpf.plot(df, type='candle', style='charles', ax=ax)

        longest_length = 0
        longest_line_data = None
        ul = df.High.max()+1
        ll = df.Low.min()-1
        inc = tick
        itr = int((ul-ll)/inc)+1

        for k in range(itr):
            lr = float(ll + k*inc)
            ur = float(lr+window)
            i = 0
            j = 0
            ct = 2

            while(i<len(df.Close) and j<len(df.Close)):
                if df.High[j] <= ur and df.Low[j] >= lr:
                    j = j+1
                elif ct <= 2 or ct <= (j-i)/10:
                    ct = ct + 1
                    j = j + 1
                else:
                    
                    line_length = j - i
                    if line_length > longest_length:
                        longest_length = line_length
                        longest_line_data = (lr , ur , i , j)
    
                    ct = 0
                    i = j

        if longest_line_data:
            lr , ur , i , j = longest_line_data
            ax.axhline(y=lr, color='b', linestyle='-', xmin=i / len(df), xmax=j / len(df))
            ax.axhline(y=ur, color='r', linestyle='-', xmin=i / len(df), xmax=j / len(df))
            ax.text(0.01 , 0.95 , f"Longest range: {longest_length} Candles" , transform=ax.transAxes , fontsize=12 , verticalalignment='top')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()

        plt.close(fig)

        return '<img src="data:image/png;base64,{}">'.format(plot_data)

if __name__ == '__main__':
    app.run(debug=True)
