import gdspy


nw_cell=gdspy.Cell('Nanowire')

def generate_nw(line, gap, area, prox_buffer=0.5, end=0.5, start_point=(0,0), round_ends=True):
    points=[start_point]
    number_of_lines = (area/((2*gap)+(2*line)))
    print(number_of_lines)
    current_x, current_y = 0,0
    #draw buffer side first
    current_y+=(area+(2*prox_buffer)+line)
    points.append((current_x, current_y))
    current_x+=(area+prox_buffer-end)
    points.append((current_x, current_y))
    current_y-=prox_buffer
    points.append((current_x, current_y))
    current_x-=(area-end)
    points.append((current_x, current_y))
    for i in range(int(round(number_of_lines))):
        current_y-=((2*line)+gap)
        points.append((current_x, current_y))
        current_x+=(area-end-prox_buffer)
        points.append((current_x, current_y))
        current_y-=gap
        points.append((current_x, current_y))
        current_x-=(area-end-prox_buffer)
        points.append((current_x, current_y))
    current_y-=(prox_buffer+line)
    points.append((current_x, current_y))

    poly=gdspy.Polygon(points)
    if round_ends==True:
    	poly.fillet((gap/2))

    #copy and rotate the nanowire and slot it in
    poly2 = gdspy.Polygon(points)
    if round_ends==True:
    	poly2.fillet((gap/2))
    poly2.rotate(3.1415)
    poly2.translate((area+(2*prox_buffer)),(area+(2*prox_buffer)+line)) 

    nw=gdspy.PolygonSet([poly, poly2])

    return poly, poly2



nw1_1, nw1_2=generate_nw(0.05,0.1, 10.2)

nw_cell.add([nw1_1,nw1_2])
gdspy.LayoutViewer()