import sys, os
import win32com.client

path = sys.argv[1]
app = win32com.client.DispatchEx('Word.Application')
app.Visible = False
try:
    doc = app.Documents.Open(path, ReadOnly=False)
    pdf = os.path.splitext(path)[0] + '.pdf'
    doc.ExportAsFixedFormat(pdf, 17)
    print('pages', doc.ComputeStatistics(2))
    doc.Close(False)
    print('exported', os.path.basename(pdf))
finally:
    try:
        app.Quit()
    except Exception:
        pass
