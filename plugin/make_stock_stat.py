import sys, win32com.client

def make_stock_stat(fn):
    open(fn)
    data = [line.split('\t') for line in open(fn).read().splitlines() if '\t' in line]
    '''
    all_date = {d:0. for d in list(set([i[0] for i in data]))}
    all_stock = list(set([i[1] for i in data]))
    table={s:all_date.copy() for s in all_stock}
    for line in data:
        table[line[1]][line[0]]=line[6]
    #print(table)
    print('\t'+'\t'.join(all_date.keys()))
    for stock,line in table.items():
        print(stock+'\t'+'\t'.join([str(i) for i in line.values()]))
    '''
    all_stock = {i[1]:0. for i in data}
    all_date = list({i[0]:None for i in data})
    table={d:all_stock.copy() for d in all_date}
    for line in data:
        table[line[0]][line[1]]=line[6]
    #print(table)
    print('\t'+'\t'.join(all_stock.keys()))
    for date,line in table.items():
        print(date+'\t'+'\t'.join([str(i).replace('.',',') for i in line.values()]))

    try:
        xlsapp = win32com.client.gencache.EnsureDispatch("Excel.Application") # Если создавать COM объект так то Sheets.Add отрабатывает правильно
    except AttributeError:
        print(f'Проблемы с gen_py пробуем очистить {win32com.gen_py.__path__}')
        sys.exit()
    xlsapp.Visible = True # Окно EXCEL видимое
    xlsapp.DisplayAlerts = False # Подавить ошибки
    wb_res=xlsapp.Workbooks.Add()


    rng = wb_res.Sheets[1].Range(wb_res.Sheets[1].Cells(1,2),wb_res.Sheets[1].Cells(1,len(all_stock.keys())+1))
    rng.Value=tuple(all_stock.keys())
    #wb_res.Sheets[1].Range('A1:D1').Value=('H1','H2','H3','H4',)
    wb_res.Sheets[1].Select()
    xlsapp.ActiveWindow.SplitColumn = 0
    xlsapp.ActiveWindow.SplitRow = 1
    xlsapp.ActiveWindow.FreezePanes = True
    wb_res.Sheets[1].Columns.AutoFilter(Field=1)
    #wb_res.Sheets[1].Columns(wb_res.Sheets[1].Columns(1),wb_res.Sheets[1].Columns(len(all_stock.keys())+2)).AutoFilter(Field=1)
    for num,(date,line) in enumerate(table.items()):
        wb_res.Sheets[1].Cells(num+2,1).Value = date
        wb_res.Sheets[1].Range(wb_res.Sheets[1].Cells(num+2,2),wb_res.Sheets[1].Cells(num+2,len(all_stock.keys())+1)).Value=tuple(line.values())

if __name__ == '__main__':
    make_stock_stat(sys.argv[1])