# The MIT License (MIT)
# 
# Copyright (c) 2016 Alex Mykyta
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#==============================================================================
# Creates a mechanism where Python classes can be converted to/from primitive
# data types.
# This is used as an intermediate layer to JSON encoding/decoding
# 

def get_all_subclasses(cls):
    all_subclasses = []
    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return(list(set(all_subclasses)))
    
#-------------------------------------------------------------------------------
def get_classid_str(cls):
    return("%s.%s" % (cls.__module__, cls.__name__))

#-------------------------------------------------------------------------------
def is_in_list(obj, obj_list):
    """
    Check if obj is in obj_list explicitly by id
    Using (obj in obj_list) has false positives if the object overrides its __eq__ operator
    """
    for o in obj_list:
        if(id(o) == id(obj)):
            return(True)
    else:
        return(False)

#-------------------------------------------------------------------------------
class Ref:
    """
    Temporary placeholder for unresolved references
    """
    def __init__(self, ref_id):
        self.ref_id = ref_id
        
#-------------------------------------------------------------------------------
def do_encode(obj, tmpl, parent_key, _encoded_objs, depth = 1):
    
    if(type(tmpl) == list):
        # Expecting a list of items
        if(type(obj) != list):
            raise TypeError("'%s', depth=%d: Expected 'list'. Got '%s'" 
                % (parent_key, depth, type(obj).__name__))
        
        # Template list must have exactly one item
        if(len(tmpl) != 1):
            raise ValueError("'%s', depth=%d: Templates for lists must have exactly one item in them"
                % (parent_key, depth))
        
        result = []
        for item in obj:
            result.append(do_encode(item, tmpl[0], parent_key, _encoded_objs, depth+1))
    
    elif(type(tmpl) == tuple):
        # Expecting a tuple of items
        if(type(obj) != tuple):
            raise TypeError("'%s', depth=%d: Expected 'tuple'. Got '%s'" 
                % (parent_key, depth, type(obj).__name__))
        
        # Size of tuples must match
        if(len(tmpl) != len(obj)):
            raise ValueError("'%s', depth=%d: Tuple len(%d) does not match template len(%d)"
                % (parent_key, depth, len(obj), len(tmpl)))
        
        tmplist = []
        for item in obj:
            tmplist.append(do_encode(item, tmpl[0], parent_key, _encoded_objs, depth+1))
        
        result = tuple(tmplist)
        
    elif(type(tmpl) == dict):
        # Expecting a dictionary
        if(type(obj) != dict):
            raise TypeError("'%s', depth=%d: Expected 'dict'. Got '%s'" 
                % (parent_key, depth, type(obj).__name__))
        
        # Template dict must have exactly one key:value pair
        if(len(tmpl) != 1):
            raise ValueError("'%s', depth=%d: Templates for dicts must have exactly one key:value pair"
                % (parent_key, depth))
        
        tmpl_k = list(tmpl.keys())[0]
        tmpl_v = list(tmpl.values())[0]
        
        result = {}
        for obj_k, obj_v in obj.items():
            k = do_encode(obj_k, tmpl_k, parent_key, _encoded_objs, depth+1)
            v = do_encode(obj_v, tmpl_v, parent_key, _encoded_objs, depth+1)
            result[k] = v
        
    elif(type(tmpl) == type):
        # Got to maximum depth.
        
        if(issubclass(tmpl, ForeignObjectCodec)):
            # Foreign object. Use template codec to translate object.
            
            # make sure the object is compatible with what the codec wants
            if(not tmpl.is_compatible(obj)):
                raise TypeError("'%s', depth=%d: Expected '%s'. Got '%s'" 
                    % (parent_key, depth, tmpl.obj_type.__name__, type(obj).__name__))
            
            result = tmpl.encode(obj)
            
        elif(issubclass(tmpl, EncodableClass)):
            # Got an EncodableClass
            
            # make sure it is what the template expects
            if(not issubclass(type(obj), tmpl)):
                raise TypeError("'%s', depth=%d: Expected '%s'. Got '%s'" 
                    % (parent_key, depth, tmpl.__name__, type(obj).__name__))
            
            result = obj.to_dict(_encoded_objs)
        
        else:
            # Everything else
            
            # types should match (unless it is None. Thats OK)
            if((type(obj) != tmpl) and (obj != None)):
                raise TypeError("'%s', depth=%d: Expected '%s'. Got '%s'" 
                    % (parent_key, depth, tmpl.__name__, type(obj).__name__))
            
            # Pass-through
            result = obj
        
    else:
        raise TypeError("'%s', depth=%d: Unsupported type '%s'" 
                    % (parent_key, depth, type(tmpl).__name__))
    
    return(result)
    
#-------------------------------------------------------------------------------
def do_decode(obj, tmpl, parent_key, _decoded_objs, depth = 1):
    
    if(type(tmpl) == list):
        # Expecting a list of items
        if(type(obj) != list):
            raise TypeError("'%s', depth=%d: Expected 'list'. Got '%s'" 
                % (parent_key, depth, type(obj).__name__))
        
        # Template list must have exactly one item
        if(len(tmpl) != 1):
            raise ValueError("'%s', depth=%d: Templates for lists must have exactly one item in them"
                % (parent_key, depth))
        
        result = []
        for item in obj:
            result.append(do_decode(item, tmpl[0], parent_key, _decoded_objs, depth+1))
    
    elif(type(tmpl) == tuple):
        # Expecting a tuple of items (a list is OK too...)
        if((type(obj) != tuple) and (type(obj) != list)):
            raise TypeError("'%s', depth=%d: Expected 'tuple' or 'list'. Got '%s'"
                % (parent_key, depth, type(obj).__name__))
        
        # Size of tuples must match
        if(len(tmpl) != len(obj)):
            raise ValueError("'%s', depth=%d: Tuple len(%d) does not match template len(%d)"
                % (parent_key, depth, len(obj), len(tmpl)))
        
        tmplist = []
        for idx, item in enumerate(obj):
            tmplist.append(do_decode(item, tmpl[idx], parent_key, _decoded_objs, depth+1))
        
        result = tuple(tmplist)
        
    elif(type(tmpl) == dict):
        # Expecting a dictionary
        if(type(obj) != dict):
            raise TypeError("'%s', depth=%d: Expected 'dict'. Got '%s'" 
                % (parent_key, depth, type(obj).__name__))
        
        # Template dict must have exactly one key:value pair
        if(len(tmpl) != 1):
            raise ValueError("'%s', depth=%d: Templates for dicts must have exactly one key:value pair"
                % (parent_key, depth))
        
        tmpl_k = list(tmpl.keys())[0]
        tmpl_v = list(tmpl.values())[0]
        
        result = {}
        for obj_k, obj_v in obj.items():
            k = do_decode(obj_k, tmpl_k, parent_key, _decoded_objs, depth+1)
            v = do_decode(obj_v, tmpl_v, parent_key, _decoded_objs, depth+1)
            result[k] = v
    
    elif(type(tmpl) == type):
        # Got to maximum depth.
        
        if(issubclass(tmpl, ForeignObjectCodec)):
            # Foreign object. Use template codec to translate object.
            result = tmpl.decode(obj)
            
        elif(issubclass(tmpl, EncodableClass)):
            # Expecting an EncodableClass
            
            # Check if current obj looks like an EncodableClass
            if((type(obj) != dict) or ('<classtype>' not in obj)):
                raise TypeError("'%s', depth=%d: Dictionary incompatible with '%s'"
                    % (parent_key, depth, tmpl.__name__))
            
            if('<ref_id>' not in obj):
                raise ValueError("'%s', depth=%d: Missing <ref_id>" % (parent_key, depth))
            
            if(obj['<classtype>'] == '<ref>'):
                # This is a reference, not an actual class definition
                # Populate a Ref object for now. It will be resolved later with the actual
                result = Ref(obj['<ref_id>'])
                
            else:
                # Not a reference. This is an actual class definition
                
                # Figure out what specific subtype of tmpl should be created.
                subclasses = [tmpl]
                subclasses.extend(get_all_subclasses(tmpl))
                
                m = list(filter(lambda cls: (get_classid_str(cls) == obj['<classtype>']), subclasses))
                if(len(m) == 0):
                    raise TypeError("'%s', depth=%d: Type '%s' is incompatible with '%s'"
                        % (parent_key, depth, obj['<classtype>'], get_classid_str(tmpl)))
                
                cls = m[0]
                result = cls.from_dict(obj, _decoded_objs)
        
        else:
            # Everything else
            
            # types should match (unless it is None. Thats OK)
            if((type(obj) != tmpl) and (obj != None)):
                raise TypeError("'%s', depth=%d: Expected '%s'. Got '%s'" 
                    % (parent_key, depth, tmpl.__name__, type(obj).__name__))
            
            # Pass-through
            result = obj
        
    else:
        raise TypeError("'%s', depth=%d: Unsupported type '%s'" 
                    % (parent_key, depth, type(tmpl).__name__))
    
    return(result)

#-------------------------------------------------------------------------------
def do_resolve_ref(tmpl, obj, _decoded_objs):
    # Note: type checking against template is only done for Refs since everything else has
    # already been validated
    
    if(type(obj) == list):
        # Resolve all refs in a list
        for i,v in enumerate(obj):
            obj[i] = do_resolve_ref(tmpl[0], v, _decoded_objs)
    
    elif(type(obj) == tuple):
        # Resolve all refs in a tuple
        
        # Cast tuple back to list so it can be modified
        obj = list(obj)
        for i, v in enumerate(obj):
            obj[i] = do_resolve_ref(tmpl[i], v, _decoded_objs)
        obj = tuple(obj)
        
    elif(type(obj) == Ref):
        # Resolve reference
        
        if(obj.ref_id not in _decoded_objs):
            raise ValueError("Unresolved reference to object with ref_id %d" % Ref.ref_id)
        
        obj = _decoded_objs[obj.ref_id]
        
        # Verify that the referenced object type is compatible with the template
        subclasses = [tmpl]
        subclasses.extend(get_all_subclasses(tmpl))
        m = list(filter(lambda cls: (cls == type(obj)), subclasses))
        if(len(m) == 0):
            raise TypeError("Referenced type '%s' is incompatible with '%s'"
                % (get_classid_str(type(obj)), get_classid_str(tmpl)))
        
    elif(issubclass(type(obj), EncodableClass)):
        # Resolve references of sub-object
        obj._resolve_refs(_decoded_objs)
        
    else:
        # Everything else passes through
        pass
    
    return(obj)
    
#-------------------------------------------------------------------------------
class ForeignObjectCodec:
    """
    Template for an object that is not an EncodableClass, nor is it a primitive datatype
    This is used to define encode/decode methods for any other types.
    """
    obj_type = type
    
    @classmethod
    def is_compatible(cls, obj):
        """
        Checks if obj is compatible with cls.obj_type.
        Override if comparison is more complex than just type-matching.
        """
        if(type(obj) != cls.obj_type):
            return(False)
        return(True)
            
    @classmethod
    def encode(cls, obj):
        """
        Convert the object obj of type cls.obj_type to a primitive datatype
        that can be used later to re-create the object.
        """
        return("NULL")
    
    @classmethod
    def decode(cls, d):
        """
        Create an object of type cls.obj_type from d
        """
        return(None)

#-------------------------------------------------------------------------------
class EncodableClass:
    
    """
    This class enables an object to be encoded and rebuilt to/from a set of primitive datatypes
    in a controlled manner.
    
    The class parameter, "encode_schema" strictly defines the type structure of the class contents
    
    encode_schema is a dictionary of class members to encode, and their template:
        {key : template}
    
        key: The name of the class member
        template: Minimal representation of the type of the member's contents
        
        Allowed aggregate data types in template:
            List: Describes a list where each item in the list is of the same type
            Tuple: Describes a tuple of fixed size, containing the matching type items
            Dict: Describes a dictionary where the keys all have the same type, as well as the values
                FYI: dictionary keys are always encoded as strings with JSON, so other datatypes will
                     not work here.
        
        Examples:
            A String:
                {"my_string" : str}
            List of integers:
                {"my_list" : [int]}
            List of mixed tuples:
                {"my_complex_list" : [(int, str, MyClass)]}
            Dictionary where the key is a string, and value is a subclass:
                {"my_dict" : {str, MyClass}}
    """
    encode_schema = {}
    
    def to_dict(self, _encoded_objs=None):
        """
        Encodes the class, and all its child members to a dictionary
        Only encodes strictly according to what is defined in encode_schema
        
        The _encoded_objs parameter is for internal use only
        (tracks which objs have already been encoded)
        """
        
        if(_encoded_objs == None):
            # Allocate new list
            _encoded_objs = []
        
        D = {}
        if(is_in_list(self, _encoded_objs)):
            # This object has already been encoded elsewhere.
            # Instead, just store a reference to the other one
            D['<classtype>'] = '<ref>'
            D['<ref_id>'] = _encoded_objs.index(self)
            
        else:
            # First time encountering this object.
            
            # Since it will be encoded here, insert into the _encoded_objs list
            ref_id = len(_encoded_objs)
            _encoded_objs.append(self)
            
            # Collapse all schemas from parent classes into one
            schema = self._merge_schemas()
            
            D['<classtype>'] = get_classid_str(type(self))
            D['<ref_id>'] = ref_id
            
            for key, template in schema.items():
                D[key] = do_encode(getattr(self,key), template, key, _encoded_objs)
        
        return(D)
    
    @classmethod
    def from_dict(cls, D, _decoded_objs=None):
        """
        Construct a class from a dictionary.
        Class members are populated based on what is defined in encode_schema
        
        The _decoded_objs parameter is for internal use only
        (tracks which objs have been decoded for later ref resolution.)
        """
        if(_decoded_objs == None):
            # Allocate new dict
            _decoded_objs = {}
            is_root = True
        else:
            is_root = False
        
        if(('<classtype>' not in D) or (D['<classtype>'] != get_classid_str(cls))):
            raise ValueError("Dictionary is incompatible with object '%s'" % cls.__name__)
        
        if('<ref_id>' not in D):
            raise ValueError("Missing <ref_id>")
            
        ref_id = D['<ref_id>']
        
        del D['<classtype>']
        del D['<ref_id>']
        
        # Collapse all schemas into one
        schema = cls._merge_schemas()
        
        self = cls.__new__(cls)
        
        # register the decoded object
        if(ref_id in _decoded_objs):
            # An object with the same ID was already decoded??
            raise ValueError("An object with the same <ref_id> : %d has already been decoded" % ref_id)
        _decoded_objs[ref_id] = self
        
        # Decode contents of self
        for key, template in schema.items():
            v = do_decode(D[key], template, key, _decoded_objs)
            setattr(self, key, v)
        
        if(is_root):
            # This is the root object. Finished decoding everything
            # Now, do a second pass through all objects, and resolve references
            self._resolve_refs(_decoded_objs)
            
        return(self)
    
    def _resolve_refs(self, _decoded_objs):
        
        # Collapse all schemas into one
        schema = type(self)._merge_schemas()
        
        for key, template in schema.items():
            v = getattr(self, key)
            v = do_resolve_ref(template, v, _decoded_objs)
            setattr(self, key, v)
    
    @classmethod
    def _merge_schemas(cls):
        """
        Combines own encode_schema with all parent classes
        Returns merged result
        """
        schema = {}
        for base_t in cls.__bases__:
            if(issubclass(base_t, EncodableClass)):
                schema.update(base_t._merge_schemas())
            
        schema.update(cls.encode_schema)
        return(schema)

################################################################################
# Example
################################################################################
if __name__ == '__main__':
    import json
    import filecmp
    import datetime
    
    class DatetimeCodec(ForeignObjectCodec):
        obj_type = datetime.datetime
        
        @classmethod
        def encode(cls, obj):
            return(obj.timestamp()*1000000)
        
        @classmethod
        def decode(cls, d):
            return(datetime.datetime.fromtimestamp(d/1000000))
    
    class Bar(EncodableClass):
        
        encode_schema = {
            "x": int,
            "D" : {
                str: str
            }
        }
        
        def __init__(self, x):
            self.x = x
            self.D = {}
            
    class Foo(EncodableClass):
        
        encode_schema = {
            "a": int,
            "items": [EncodableClass],
            "timestamp": DatetimeCodec
        }
        
        def __init__(self, a):
            self.a = a
            self.items = []
            self.timestamp = datetime.datetime.today()
    
    # Create a data structure
    foo = Foo(1)
    foo.items.append(Bar(100))
    foo.items.append(Bar(1234))
    b = Bar(22)
    foo.items.append(b)
    foo.items.append(b)
    b.D["hello"] = "world"
    b.D["bye"] = "asdf"
    foo2 = Foo(999)
    foo2.items.append(Bar(77))
    foo2.items.append(Bar(66))
    foo2.items.append(b)
    foo.items.append(foo2)
    foo.items.append(foo)
    
    # Convert to dict and save to file as JSON
    with open("test.json", 'w') as f:
        json.dump(foo.to_dict(), f, indent=2, sort_keys = True)
    
    # Reconstitute from file
    with open("test.json", 'r') as f:
        foo_prime = Foo.from_dict(json.load(f))
    
    # Convert back to JSON
    with open("test2.json", 'w') as f:
        json.dump(foo_prime.to_dict(), f, indent=2, sort_keys = True)
        
    if(filecmp.cmp("test.json", "test2.json")):
        print("OK!")
    else:
        print("Failed")