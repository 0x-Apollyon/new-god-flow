import ast
import random

global block_id_counter
block_id_counter = 4072007 #starting value of the block id counter

class Block:
    def __init__(self , entry_edges ,  statements , name , exit_edges=[]):
        global block_id_counter
        self.id = block_id_counter
        block_id_counter = block_id_counter + 1
        self.exit_edges = exit_edges #array 
        self.entry_edges = entry_edges #array
        self.statements = statements #array
        self.name = name #to help devs

    def is_empty(self):
        if len(self.statements) == 0:
            return True 

    def add_exit(self , block=None):
        if block:
            if block not in self.exit_edges:
                self.exit_edges.append(block)

    def add_entry(self , block=None):
        if block:
            if block not in self.entry_edges:
                self.entry_edges.append(block)

    def add_successor(self , block=None):
        if block:
            if block not in self.exit_edges:
                self.exit_edges.append(block)
                block.add_entry(self)

class CFG:
    def __init__(self , code):
        self.entry_node = Block([] , [] , "Start" , [])
        self.blocks = {self.entry_node.id : self.entry_node}
        self.current_block = self.entry_node
        
        self.statement_nodes = {"Assign" , "Expr" , "AugAssign" , "AnnAssign" , "Pass" , "Import" , "ImportFrom" , "Global" , "Nonlocal" , "Delete" , "FunctionDef" , "ClassDef" , "AsyncFunctionDef" , "FormattedValue" , "JoinedStr"}
        #if something is not in any of the defined nodes we will still treat it as a statement
        code_ast = ast.parse(code)
        self.walk(code_ast)
        

    def walk(self , node):

        node_class_name = node.__class__.__name__

        if node_class_name in self.statement_nodes:
            self.visit_statement(node)
        elif node_class_name == 'If':
            self.visit_if(node)
        elif node_class_name == 'Match':
            self.visit_match(node)
        #else:
        #    self.visit_statement(node)
        #this part will be more appropriate once we have handling for enough "branch" causing stuff

        for child in ast.iter_child_nodes(node):
            self.walk(child)

    def visit_statement(self , node):
        self.current_block.statements.append(node)

    def visit_if(self , node , merge_block=None):

        self.current_block.statements.append(ast.If(test=node.test, body=[], orelse=[]))

        if_body_block = Block([], [], "IfBody", [])
        self.blocks[if_body_block.id] = if_body_block 
        

        if merge_block is None:
            merge_block = Block([], [], "Merge", [])
            self.blocks[merge_block.id] = merge_block

        decision_block = self.current_block
        decision_block.add_successor(if_body_block)

        self.current_block = if_body_block
        for stmt in node.body:
            self.walk(stmt)

        if self.current_block:
            self.current_block.add_successor(merge_block)

        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                #check if its actually an elif
                self.current_block = decision_block
                self.visit_If(node.orelse[0], merge_block=merge_block)
            else:
                else_body_block = Block([], [], "ElseBody", [])
                self.blocks[else_body_block.id] = else_body_block
                decision_block.add_successor(else_body_block)

                self.current_block = else_body_block
                for stmt in node.orelse:
                    self.walk(stmt)

                if self.current_block:
                    self.current_block.add_successor(merge_block)
        else:
            decision_block.add_successor(merge_block)

        self.current_block = merge_block
        
    def visit_Match(self , node):
        self.current_block.statements.append(ast.Match(subject=node.subject, cases=[]))

        decision_block = self.current_block

        merge_block = Block([], [], "MatchMerge", [])
        self.blocks[merge_block.id] = merge_block

        for case in node.cases:
            case_body_block = Block([], [], "CaseBody", [])
            self.blocks[case_body_block.id] = case_body_block

            decision_block.add_successor(case_body_block)

            case_body_block.statements.append(ast.MatchCase(pattern=case.pattern, guard=case.guard, body=[]))

            self.current_block = case_body_block
            for stmt in case.body:
                self.walk(stmt)

            if self.current_block:
                self.current_block.add_successor(merge_block)

        decision_block.add_successor(merge_block)
        self.current_block = merge_block



code = """
x = 1
y = x + 10
if x == 10:
    print("a")
"""

cfg = CFG(code)
print(ast.unparse(cfg.blocks[4072007].statements))
    