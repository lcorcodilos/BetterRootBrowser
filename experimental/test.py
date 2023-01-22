from BetterRootBrowser import graph, data
import dash

file = data.open_file('~/CMS/temp/nano_4.root')
print (file['Events']['data'].to_json(orient='records'))
table = graph.make_table(file['Events'])
