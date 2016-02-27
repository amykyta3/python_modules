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
def do_encode(obj, tmpl, parent_key, depth = 1,):
    
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
            result.append(do_encode(item, tmpl[0], parent_key, depth+1))
    
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
            tmplist.append(do_encode(item, tmpl[0], parent_key, depth+1))
        
        result = tuple(tmplist)
        
    elif(type(tmpl) == type):
        # Got to maximum depth.
        
        if(issubclass(type(obj), encodable_class)):
            # Got an encodable_class
            
            # make sure it is what the template expects
            if(not issubclass(type(obj), tmpl)):
                raise TypeError("'%s', depth=%d: Expected '%s'. Got '%s'" 
                    % (parent_key, depth, tmpl.__name__, type(obj).__name__))
            
            result = obj.to_dict()
        
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
def do_decode(obj, tmpl, parent_key, depth = 1,):
    
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
            result.append(do_decode(item, tmpl[0], parent_key, depth+1))
    
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
        for item in obj:
            tmplist.append(do_decode(item, tmpl[0], parent_key, depth+1))
        
        result = tuple(tmplist)
        
    elif(type(tmpl) == type):
        # Got to maximum depth.
        
        if(issubclass(tmpl, encodable_class)):
            # Expecting an encodable_class
            
            # Check if current obj looks like an encodable_class
            if((type(obj) != dict) or ('__classtype__' not in obj)):
                raise TypeError("'%s', depth=%d: Dictionary incompatible with '%s'"
                    % (parent_key, depth, tmpl.__name__))
            
            # Figure out what specific subtype of tmpl should be created.
            subclasses = [tmpl]
            subclasses.extend(get_all_subclasses(tmpl))
            
            m = list(filter(lambda cls: (get_classid_str(cls) == obj['__classtype__']), subclasses))
            if(len(m) == 0):
                raise TypeError("'%s', depth=%d: Type '%s' is incompatible with '%s'"
                    % (parent_key, depth, obj['__classtype__'], get_classid_str(tmpl)))
            
            cls = m[0]
            result = cls.from_dict(obj)
        
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
class encodable_class(object):
    
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
    _encode_schema = {}
    
    def to_dict(self):
        """
        Encodes the class, and all its child members to a dictionary
        Only encodes strictly according to what is defined in _encode_schema
        """
        # Collapse all schemas into one
        schema = self._merge_schemas()
        
        D = {}
        D['__classtype__'] = get_classid_str(type(self))
        
        for key, template in schema.items():
            D[key] = do_encode(getattr(self,key), template, key)
        
        return(D)
    
    @classmethod
    def from_dict(cls, D):
        """
        Construct a class from a dictionary.
        Class members are populated based on what is defined in _encode_schema
        """
        if(('__classtype__' not in D) or (D['__classtype__'] != get_classid_str(cls))):
            raise ValueError("Dictionary is incompatible with object '%s'" % cls.__name__)
        
        del D['__classtype__']
        
        # Collapse all schemas into one
        schema = cls._merge_schemas()
        
        self = cls.__new__(cls)
        
        for key, template in schema.items():
            setattr(self, key, do_decode(D[key], template, key))
        
        return(self)
    
    @classmethod
    def _merge_schemas(cls):
        """
        Combines own _encode_schema with all parent classes
        Returns merged result
        """
        schema = {}
        for base_t in cls.__bases__:
            if(issubclass(base_t, encodable_class)):
                schema.update(base_t._merge_schemas())
            
        schema.update(cls._encode_schema)
        return(schema)
