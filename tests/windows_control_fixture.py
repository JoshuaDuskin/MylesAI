"""Disposable real Windows windows; contains no user files or application state."""
import json, pathlib, sys, tkinter as tk

def main():
    ready=pathlib.Path(sys.argv[1]);stop=pathlib.Path(sys.argv[2])
    root=tk.Tk();root.withdraw()
    for label in ['Alpha','Beta','Unsaved']:
        window=tk.Toplevel(root);window.title('MYLES_CONTROL_QA '+label);window.geometry('420x150+100+100')
        tk.Label(window,text='Disposable Myles desktop test: '+label).pack(pady=20)
        if label=='Unsaved':
            tk.Label(window,text='Unsaved test document. Close confirmation required.').pack()
            window.protocol('WM_DELETE_WINDOW',lambda:None)
    root.update();ready.write_text(json.dumps({'ready':True}))
    def poll():
        if stop.exists():root.destroy()
        else:root.after(100,poll)
    root.after(100,poll);root.after(120000,root.destroy);root.mainloop()

if __name__=='__main__':main()
