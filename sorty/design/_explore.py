import math
def norm(v):
    l = math.sqrt(sum(c*c for c in v)); return tuple(c/l for c in v)
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def cam(C, T, f):
    fw = norm(sub(T, C)); rt = norm(cross(fw, (0,0,1))); up = cross(rt, fw)
    def proj(P):
        d = sub(P, C); x, y, z = dot(d, rt), dot(d, up), dot(d, fw)
        return (0.5 + (f/36.0)*x/z, 0.5 - (f/36.0)*(16/9.0)*y/z, z)
    return proj
def setup(phi, R, T, h, f, person):
    C = (T[0] + R*math.sin(math.radians(phi)), T[1] - R*math.cos(math.radians(phi)), h)
    pr = cam(C, T, f)
    px, py = person
    hx, hy = 0.0, 0.17
    yaw = math.atan2(hx-px, hy-py)
    fwd = (math.sin(yaw), math.cos(yaw)); rgt = (math.cos(yaw), -math.sin(yaw))
    def pl(lx, ly, lz):   # person-local (x right, y forward) -> world
        return (px + rgt[0]*lx + fwd[0]*ly, py + rgt[1]*lx + fwd[1]*ly, lz)
    pts = {
      "person_feet": pl(0,0,0), "person_head_top": pl(0,0.01,1.725), "shoulderL": pl(-0.26,0,1.4), "shoulderR": pl(0.26,0,1.4),
      "hands_mid": pl(0,0.40,1.20), "handL": pl(-0.14,0.40,1.2), "handR": pl(0.14,0.40,1.2),
      "zone_near": (px + 0.43, py - 0.6, 0), "zone_farleft": (px - 0.43, py + 0.29, 0),
      "rec_open": (-0.51,-0.1125,0.87), "com_open": (0,-0.1125,0.87), "lan_open": (0.51,-0.1125,0.87),
      "rec_front_left_bot": (-0.755,-0.225,0.0), "rec_front_left_top": (-0.755,-0.225,0.74), "lan_back_right_top": (0.755,0.225,1.0),
      "lan_front_right_bot": (0.755,-0.225,0.0), "head_top": (0,0.19,1.63), "screen_c": (0,0.17,1.50), "planter": (1.42,0.08,0.9), "planter_top": (1.6,0.08,1.4),
    }
    print("phi=%s R=%s T=%s h=%s f=%s person=%s  C=(%.2f,%.2f,%.2f) yaw=%.1f" % (phi,R,T,h,f,person,C[0],C[1],C[2],math.degrees(yaw)))
    for k,P in pts.items():
        u,v,z = pr(P); print("   %-22s u=%.3f v=%.3f depth=%.2f" % (k,u,v,z))
import sys
setup(40, 5.0, (0.15,-0.45,0.85), 1.9, 40, (-0.75,-1.0))
setup(40, 5.3, (0.05,-0.55,0.85), 1.9, 42, (-0.75,-1.05))
setup(42, 5.3, (0.05,-0.55,0.85), 2.0, 42, (-0.7,-1.1))
print("=========== refined ===========")
setup(40, 5.0, (0.15,-0.45,0.85), 1.9, 48, (-0.75,-1.0))
setup(40, 5.0, (0.25,-0.45,0.80), 1.95, 48, (-0.75,-1.0))
setup(40, 4.8, (0.25,-0.45,0.78), 2.0, 46, (-0.75,-1.0))
