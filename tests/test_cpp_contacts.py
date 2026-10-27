"""Physical invariants and shared-initial-state checks for the C++ motion port."""
import math
import unittest
import numpy as np
from rotary_melter.Configuration import load_inputs
from rotary_melter.NativeEngine import library_path
from rotary_melter.dynamics.NativeContactEngine import NativeContacts
from rotary_melter.dynamics.ContactDynamics import DEM, liquid_plane
from rotary_melter.dynamics.RigidBodyDynamics import integrate_rigid, new_warm_history
from rotary_melter.dynamics.FastContactDynamics import integrate_fast
from numba import types
from numba.typed import Dict


@unittest.skipUnless(library_path().exists(), 'Build the native engine first')
class NativeContactTests(unittest.TestCase):
    def setUp(self):
        self.configuration=load_inputs()['inputs']
        self.context=NativeContacts()
        self.addCleanup(self.context.close)
        self.g=np.array([.3,.8,.15,1,math.sqrt(.5),math.sqrt(.5),2e7,.45,.35,.25,2/7,.01,0,4,.35,.9])

    def advance(self,p,steps=1,rigid=True,gravity=0,dt=1/960,first=0):
        return self.context.advance(p,.0075,self.g,steps,dt,0.,64,12,first,rigid,gravity)

    def test_analytic_restitution_and_linear_momentum(self):
        self.g[7:9]=0;self.g[9]=.5
        p=np.zeros((2,12));p[:,2]=.4;p[:,0]=[-.0075,.0075];p[:,3]=[.1,-.1]
        self.advance(p)
        np.testing.assert_allclose(p[:,3],[-.05,.05],atol=1e-12,rtol=0)
        self.assertAlmostEqual(p[:,3].sum(),0,places=12)

    def test_inclined_free_fall(self):
        p=np.zeros((1,12));p[0,2]=.4
        self.advance(p,96,gravity=9.81)
        np.testing.assert_allclose(p[0,4:6],[-9.81/math.sqrt(2)*.1]*2,atol=1e-12,rtol=0)

    def test_friction_preserves_angular_and_linear_momentum(self):
        p=np.zeros((2,12));p[:,2]=.4;p[:,0]=[-.0075,.0075];p[:,3]=[.1,-.1];p[0,4]=.08
        def angular(q):return np.cross(q[:,:3],q[:,3:6]).sum(axis=0)+.4*.0075**2*q[:,6:9].sum(axis=0)
        initial=angular(p);momentum=p[:,3:6].sum(axis=0)
        self.advance(p)
        np.testing.assert_allclose(angular(p),initial,atol=1e-12,rtol=0)
        np.testing.assert_allclose(p[:,3:6].sum(axis=0),momentum,atol=1e-12,rtol=0)

    def test_rigid_port_matches_reference_from_shared_state(self):
        p=np.zeros((3,12));p[:,2]=.4;p[:,0]=[-.015,0,.015];p[:,1]=-.2925;p[:,3]=[.1,0,-.1];p[0,4]=.08
        reference=p.copy();warm=new_warm_history()
        for first in (0,10):
            self.advance(p,10,gravity=9.81,first=first)
            integrate_rigid(reference,.0075,self.g,10,1/960,0.,64,12,9.81,warm,first)
            np.testing.assert_allclose(p,reference,atol=2e-10,rtol=1e-9)

    def test_compliant_port_matches_reference_from_shared_state(self):
        p=np.zeros((2,12));p[:,2]=.4;p[:,0]=[-.00745,.00745];p[:,1]=-.2925;p[:,3]=[.1,-.1];p[0,4]=.08
        reference=p.copy();history=Dict.empty(types.int64,types.UniTuple(types.float64,4))
        for first in (0,10):
            self.advance(p,10,rigid=False,gravity=9.81,dt=.00002,first=first)
            integrate_fast(reference,.0075,self.g,history,first,10,.00002,0.)
            np.testing.assert_allclose(p,reference,atol=2e-10,rtol=1e-9)

    def test_liquid_root_and_native_lattice(self):
        c={**self.configuration,'diameter':120,'length':160,'headDepth':30,'targetFill':.3}
        d=DEM(c,{'liquid':.1,'settle':0,'solver':'rigid'})
        self.assertIsNotNone(d.native)
        volume=d.mass*d.liquid/c['rhol']
        expected=liquid_plane(d.p,d.r,*d.g[:6],volume)
        self.assertAlmostEqual(d.native.liquid_plane(d.p,d.r,d.g,volume),expected,places=9)
        self.assertTrue(np.isfinite(d.p).all())
        d.advance(20)
        self.assertEqual(d.metrics()['backend'],'cpp')
        self.assertEqual(d.escaped,0)
