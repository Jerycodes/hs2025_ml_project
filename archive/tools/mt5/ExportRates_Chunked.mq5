// ExportRates_Chunked.mq5
// Robust CSV export of historical bars from MetaTrader 5 (chunked to avoid CopyRates limits).

#property script_show_inputs

input string          InpSymbol          = "EURUSD";
input ENUM_TIMEFRAMES InpTF              = PERIOD_M1;
input datetime        InpFrom            = D'2020.01.01 00:00';
input datetime        InpTo              = D'2025.12.31 23:59';
input string          InpOutFile         = "EURUSD_M1_2020_2025.csv";
input bool            InpUseCommonFolder = true;      // true => Common\\Files, false => Terminal\\MQL5\\Files
input int             InpChunkBars       = 100000;    // bars per CopyRates() call (reduce if you get memory issues)
input bool            InpOverwrite       = true;      // false => append if file exists
input bool            InpWriteHeader     = true;
input int             InpRetrySeconds    = 60;        // wait/retry if history is still updating (Error 4401)

void OnStart()
{
   if(InpFrom >= InpTo)
   {
      Print("Invalid range: InpFrom must be < InpTo");
      return;
   }

   int chunk_bars = InpChunkBars;
   if(chunk_bars <= 0)
      chunk_bars = 100000;

   int retry_seconds = InpRetrySeconds;
   if(retry_seconds < 0)
      retry_seconds = 0;

   if(!SymbolSelect(InpSymbol, true))
   {
      Print("SymbolSelect failed for ", InpSymbol, " Error=", GetLastError());
      return;
   }

   const int digits = (int)SymbolInfoInteger(InpSymbol, SYMBOL_DIGITS);
   const int tf_sec = PeriodSeconds(InpTF);
   if(tf_sec <= 0)
   {
      Print("Unsupported timeframe (PeriodSeconds<=0).");
      return;
   }

   // Use FILE_ANSI for maximum compatibility across MT5 builds.
   // We only write numbers/ASCII anyway, so encoding is not critical.
   const int common_flag = (InpUseCommonFolder ? FILE_COMMON : 0);
   const int flags = FILE_CSV | FILE_ANSI | common_flag;

   int handle = INVALID_HANDLE;

   if(!InpOverwrite)
   {
      // Append mode: open existing file read/write and seek to end; otherwise create new.
      ResetLastError();
      if(FileIsExist(InpOutFile, common_flag))
      {
         handle = FileOpen(InpOutFile, FILE_READ | FILE_WRITE | flags, ',');
         if(handle != INVALID_HANDLE)
            FileSeek(handle, 0, SEEK_END);
      }
   }

   if(handle == INVALID_HANDLE)
   {
      ResetLastError();
      handle = FileOpen(InpOutFile, FILE_WRITE | flags, ',');
   }

   if(handle == INVALID_HANDLE)
   {
      Print("FileOpen failed. Error=", GetLastError());
      return;
   }

   if(InpWriteHeader && (InpOverwrite || FileTell(handle) == 0))
   {
      FileWrite(handle,
         "time_unix",
         "time",
         "open","high","low","close",
         "tick_volume","spread","real_volume"
      );
   }

   MqlRates rates[];
   ArraySetAsSeries(rates, false);

   datetime cursor = InpFrom;
   datetime last_written_time = 0;
   long total_written = 0;
   int loops = 0;

   while(cursor <= InpTo)
   {
      loops++;
      if(loops > 100000)
      {
         Print("Safety break (too many loops).");
         break;
      }

      ResetLastError();
      int copied = -1;
      for(int attempt = 0; attempt <= retry_seconds; attempt++)
      {
         ResetLastError();
         copied = CopyRates(InpSymbol, InpTF, cursor, chunk_bars, rates);
         if(copied > 0)
            break;

         int err = GetLastError();
         // 4401 is commonly seen while terminal is still downloading/synchronizing history.
         if(err == 4401 && attempt < retry_seconds)
         {
            if(attempt == 0)
               Print("History updating (Error=4401). Waiting up to ", retry_seconds, "s ...");
            Sleep(1000);
            continue;
         }

         Print("CopyRates failed (copied=", copied, "). Error=", err,
               ". Tip: Open a chart for the symbol/TF and scroll back to force history download.");
         break;
      }

      if(copied <= 0)
      {
         break;
      }

      datetime chunk_last_time = 0;
      for(int i = 0; i < copied; i++)
      {
         datetime t = rates[i].time;
         if(t > InpTo)
            break;
         if(t <= last_written_time)
            continue; // avoid duplicates when chunks overlap

         FileWrite(handle,
            (long)t,
            TimeToString(t, TIME_DATE | TIME_MINUTES | TIME_SECONDS),
            DoubleToString(rates[i].open,  digits),
            DoubleToString(rates[i].high,  digits),
            DoubleToString(rates[i].low,   digits),
            DoubleToString(rates[i].close, digits),
            (long)rates[i].tick_volume,
            (int)rates[i].spread,
            (long)rates[i].real_volume
         );

         last_written_time = t;
         chunk_last_time = t;
         total_written++;
      }

      FileFlush(handle);

      if(chunk_last_time <= 0)
      {
         Print("No new bars written for cursor=", TimeToString(cursor, TIME_DATE|TIME_MINUTES|TIME_SECONDS), ". Stopping.");
         break;
      }

      if(chunk_last_time >= InpTo)
         break;

      datetime next_cursor = chunk_last_time + tf_sec;
      if(next_cursor <= cursor)
      {
         Print("Cursor did not advance (cursor=", cursor, " next=", next_cursor, "). Stopping.");
         break;
      }
      cursor = next_cursor;

      if((total_written % 200000) == 0)
      {
         Print("Progress: written=", total_written,
               " last=", TimeToString(last_written_time, TIME_DATE|TIME_MINUTES|TIME_SECONDS));
      }
   }

   FileClose(handle);
   Print("Export done: ", InpOutFile, " rows=", total_written,
         " folder=", (InpUseCommonFolder ? "Common\\Files" : "Terminal\\MQL5\\Files"));
}
