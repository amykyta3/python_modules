# 
# Creates a mechanism where Python classes can be converted to <--> from primitive data types
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
        
    elif(type(tmpl) == type):
        # Got to maximum depth.
        
        if(issubclass(type(obj), EncodableClass)):
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
        
    elif(type(tmpl) == type):
        # Got to maximum depth.
        
        if(issubclass(tmpl, EncodableClass)):
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
class EncodableClass(object):
    
    """
    Dictionary of class members to encode
    {key : template}
    
    key: The name of the class member
    template: Minimal representation of the type of the member's contents
    
    Aggregate data types in template:
        List: Describes a list where each item in the list is of the same type
        Tuple: Describes a tuple of fixed size, containing the matching type items
    
    Examples:
        A String:
            {"my_string" : str}
        List of integers:
            {"my_list" : [int]}
        List of mixed tuples:
            {"my_complex_list" : [(int, str, my_class)]}
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
        if(self in _encoded_objs):
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
