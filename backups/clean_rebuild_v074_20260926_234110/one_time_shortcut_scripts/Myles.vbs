Set sh=CreateObject("WScript.Shell")
Set sc=sh.CreateShortcut("C:\Users\Joshu\Desktop\Myles.lnk")
sc.TargetPath="C:\Users\Joshu\AppData\Local\MylesAI\.venv\Scripts\python.exe"
sc.Arguments="""C:\Users\Joshu\AppData\Local\MylesAI\myles_terminal.py"""
sc.WorkingDirectory="C:\Users\Joshu\AppData\Local\MylesAI"
sc.WindowStyle=1
sc.Description="Myles Owner Terminal"
sc.Save
