# Generated from Python3.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .Python3Parser import Python3Parser
else:
    from Python3Parser import Python3Parser

# This class defines a complete listener for a parse tree produced by Python3Parser.
class Python3Listener(ParseTreeListener):

    # Enter a parse tree produced by Python3Parser#single_input.
    def enterSingle_input(self, ctx:Python3Parser.Single_inputContext):
        pass

    # Exit a parse tree produced by Python3Parser#single_input.
    def exitSingle_input(self, ctx:Python3Parser.Single_inputContext):
        pass


    # Enter a parse tree produced by Python3Parser#file_input.
    def enterFile_input(self, ctx:Python3Parser.File_inputContext):
        pass

    # Exit a parse tree produced by Python3Parser#file_input.
    def exitFile_input(self, ctx:Python3Parser.File_inputContext):
        pass


    # Enter a parse tree produced by Python3Parser#eval_input.
    def enterEval_input(self, ctx:Python3Parser.Eval_inputContext):
        pass

    # Exit a parse tree produced by Python3Parser#eval_input.
    def exitEval_input(self, ctx:Python3Parser.Eval_inputContext):
        pass


    # Enter a parse tree produced by Python3Parser#decorator.
    def enterDecorator(self, ctx:Python3Parser.DecoratorContext):
        pass

    # Exit a parse tree produced by Python3Parser#decorator.
    def exitDecorator(self, ctx:Python3Parser.DecoratorContext):
        pass


    # Enter a parse tree produced by Python3Parser#decorators.
    def enterDecorators(self, ctx:Python3Parser.DecoratorsContext):
        pass

    # Exit a parse tree produced by Python3Parser#decorators.
    def exitDecorators(self, ctx:Python3Parser.DecoratorsContext):
        pass


    # Enter a parse tree produced by Python3Parser#decorated.
    def enterDecorated(self, ctx:Python3Parser.DecoratedContext):
        pass

    # Exit a parse tree produced by Python3Parser#decorated.
    def exitDecorated(self, ctx:Python3Parser.DecoratedContext):
        pass


    # Enter a parse tree produced by Python3Parser#funcdef.
    def enterFuncdef(self, ctx:Python3Parser.FuncdefContext):
        pass

    # Exit a parse tree produced by Python3Parser#funcdef.
    def exitFuncdef(self, ctx:Python3Parser.FuncdefContext):
        pass


    # Enter a parse tree produced by Python3Parser#parameters.
    def enterParameters(self, ctx:Python3Parser.ParametersContext):
        pass

    # Exit a parse tree produced by Python3Parser#parameters.
    def exitParameters(self, ctx:Python3Parser.ParametersContext):
        pass


    # Enter a parse tree produced by Python3Parser#typedargslist.
    def enterTypedargslist(self, ctx:Python3Parser.TypedargslistContext):
        pass

    # Exit a parse tree produced by Python3Parser#typedargslist.
    def exitTypedargslist(self, ctx:Python3Parser.TypedargslistContext):
        pass


    # Enter a parse tree produced by Python3Parser#tfpdef.
    def enterTfpdef(self, ctx:Python3Parser.TfpdefContext):
        pass

    # Exit a parse tree produced by Python3Parser#tfpdef.
    def exitTfpdef(self, ctx:Python3Parser.TfpdefContext):
        pass


    # Enter a parse tree produced by Python3Parser#varargslist.
    def enterVarargslist(self, ctx:Python3Parser.VarargslistContext):
        pass

    # Exit a parse tree produced by Python3Parser#varargslist.
    def exitVarargslist(self, ctx:Python3Parser.VarargslistContext):
        pass


    # Enter a parse tree produced by Python3Parser#vfpdef.
    def enterVfpdef(self, ctx:Python3Parser.VfpdefContext):
        pass

    # Exit a parse tree produced by Python3Parser#vfpdef.
    def exitVfpdef(self, ctx:Python3Parser.VfpdefContext):
        pass


    # Enter a parse tree produced by Python3Parser#stmt.
    def enterStmt(self, ctx:Python3Parser.StmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#stmt.
    def exitStmt(self, ctx:Python3Parser.StmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#simple_stmt.
    def enterSimple_stmt(self, ctx:Python3Parser.Simple_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#simple_stmt.
    def exitSimple_stmt(self, ctx:Python3Parser.Simple_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#small_stmt.
    def enterSmall_stmt(self, ctx:Python3Parser.Small_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#small_stmt.
    def exitSmall_stmt(self, ctx:Python3Parser.Small_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#expr_stmt.
    def enterExpr_stmt(self, ctx:Python3Parser.Expr_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#expr_stmt.
    def exitExpr_stmt(self, ctx:Python3Parser.Expr_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#testlist_star_expr.
    def enterTestlist_star_expr(self, ctx:Python3Parser.Testlist_star_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#testlist_star_expr.
    def exitTestlist_star_expr(self, ctx:Python3Parser.Testlist_star_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#augassign.
    def enterAugassign(self, ctx:Python3Parser.AugassignContext):
        pass

    # Exit a parse tree produced by Python3Parser#augassign.
    def exitAugassign(self, ctx:Python3Parser.AugassignContext):
        pass


    # Enter a parse tree produced by Python3Parser#del_stmt.
    def enterDel_stmt(self, ctx:Python3Parser.Del_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#del_stmt.
    def exitDel_stmt(self, ctx:Python3Parser.Del_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#pass_stmt.
    def enterPass_stmt(self, ctx:Python3Parser.Pass_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#pass_stmt.
    def exitPass_stmt(self, ctx:Python3Parser.Pass_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#flow_stmt.
    def enterFlow_stmt(self, ctx:Python3Parser.Flow_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#flow_stmt.
    def exitFlow_stmt(self, ctx:Python3Parser.Flow_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#break_stmt.
    def enterBreak_stmt(self, ctx:Python3Parser.Break_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#break_stmt.
    def exitBreak_stmt(self, ctx:Python3Parser.Break_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#continue_stmt.
    def enterContinue_stmt(self, ctx:Python3Parser.Continue_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#continue_stmt.
    def exitContinue_stmt(self, ctx:Python3Parser.Continue_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#return_stmt.
    def enterReturn_stmt(self, ctx:Python3Parser.Return_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#return_stmt.
    def exitReturn_stmt(self, ctx:Python3Parser.Return_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#yield_stmt.
    def enterYield_stmt(self, ctx:Python3Parser.Yield_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#yield_stmt.
    def exitYield_stmt(self, ctx:Python3Parser.Yield_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#raise_stmt.
    def enterRaise_stmt(self, ctx:Python3Parser.Raise_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#raise_stmt.
    def exitRaise_stmt(self, ctx:Python3Parser.Raise_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#import_stmt.
    def enterImport_stmt(self, ctx:Python3Parser.Import_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#import_stmt.
    def exitImport_stmt(self, ctx:Python3Parser.Import_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#import_name.
    def enterImport_name(self, ctx:Python3Parser.Import_nameContext):
        pass

    # Exit a parse tree produced by Python3Parser#import_name.
    def exitImport_name(self, ctx:Python3Parser.Import_nameContext):
        pass


    # Enter a parse tree produced by Python3Parser#import_from.
    def enterImport_from(self, ctx:Python3Parser.Import_fromContext):
        pass

    # Exit a parse tree produced by Python3Parser#import_from.
    def exitImport_from(self, ctx:Python3Parser.Import_fromContext):
        pass


    # Enter a parse tree produced by Python3Parser#import_as_name.
    def enterImport_as_name(self, ctx:Python3Parser.Import_as_nameContext):
        pass

    # Exit a parse tree produced by Python3Parser#import_as_name.
    def exitImport_as_name(self, ctx:Python3Parser.Import_as_nameContext):
        pass


    # Enter a parse tree produced by Python3Parser#dotted_as_name.
    def enterDotted_as_name(self, ctx:Python3Parser.Dotted_as_nameContext):
        pass

    # Exit a parse tree produced by Python3Parser#dotted_as_name.
    def exitDotted_as_name(self, ctx:Python3Parser.Dotted_as_nameContext):
        pass


    # Enter a parse tree produced by Python3Parser#import_as_names.
    def enterImport_as_names(self, ctx:Python3Parser.Import_as_namesContext):
        pass

    # Exit a parse tree produced by Python3Parser#import_as_names.
    def exitImport_as_names(self, ctx:Python3Parser.Import_as_namesContext):
        pass


    # Enter a parse tree produced by Python3Parser#dotted_as_names.
    def enterDotted_as_names(self, ctx:Python3Parser.Dotted_as_namesContext):
        pass

    # Exit a parse tree produced by Python3Parser#dotted_as_names.
    def exitDotted_as_names(self, ctx:Python3Parser.Dotted_as_namesContext):
        pass


    # Enter a parse tree produced by Python3Parser#dotted_name.
    def enterDotted_name(self, ctx:Python3Parser.Dotted_nameContext):
        pass

    # Exit a parse tree produced by Python3Parser#dotted_name.
    def exitDotted_name(self, ctx:Python3Parser.Dotted_nameContext):
        pass


    # Enter a parse tree produced by Python3Parser#global_stmt.
    def enterGlobal_stmt(self, ctx:Python3Parser.Global_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#global_stmt.
    def exitGlobal_stmt(self, ctx:Python3Parser.Global_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#nonlocal_stmt.
    def enterNonlocal_stmt(self, ctx:Python3Parser.Nonlocal_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#nonlocal_stmt.
    def exitNonlocal_stmt(self, ctx:Python3Parser.Nonlocal_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#assert_stmt.
    def enterAssert_stmt(self, ctx:Python3Parser.Assert_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#assert_stmt.
    def exitAssert_stmt(self, ctx:Python3Parser.Assert_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#compound_stmt.
    def enterCompound_stmt(self, ctx:Python3Parser.Compound_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#compound_stmt.
    def exitCompound_stmt(self, ctx:Python3Parser.Compound_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#if_stmt.
    def enterIf_stmt(self, ctx:Python3Parser.If_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#if_stmt.
    def exitIf_stmt(self, ctx:Python3Parser.If_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#while_stmt.
    def enterWhile_stmt(self, ctx:Python3Parser.While_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#while_stmt.
    def exitWhile_stmt(self, ctx:Python3Parser.While_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#for_stmt.
    def enterFor_stmt(self, ctx:Python3Parser.For_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#for_stmt.
    def exitFor_stmt(self, ctx:Python3Parser.For_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#try_stmt.
    def enterTry_stmt(self, ctx:Python3Parser.Try_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#try_stmt.
    def exitTry_stmt(self, ctx:Python3Parser.Try_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#with_stmt.
    def enterWith_stmt(self, ctx:Python3Parser.With_stmtContext):
        pass

    # Exit a parse tree produced by Python3Parser#with_stmt.
    def exitWith_stmt(self, ctx:Python3Parser.With_stmtContext):
        pass


    # Enter a parse tree produced by Python3Parser#with_item.
    def enterWith_item(self, ctx:Python3Parser.With_itemContext):
        pass

    # Exit a parse tree produced by Python3Parser#with_item.
    def exitWith_item(self, ctx:Python3Parser.With_itemContext):
        pass


    # Enter a parse tree produced by Python3Parser#except_clause.
    def enterExcept_clause(self, ctx:Python3Parser.Except_clauseContext):
        pass

    # Exit a parse tree produced by Python3Parser#except_clause.
    def exitExcept_clause(self, ctx:Python3Parser.Except_clauseContext):
        pass


    # Enter a parse tree produced by Python3Parser#suite.
    def enterSuite(self, ctx:Python3Parser.SuiteContext):
        pass

    # Exit a parse tree produced by Python3Parser#suite.
    def exitSuite(self, ctx:Python3Parser.SuiteContext):
        pass


    # Enter a parse tree produced by Python3Parser#test.
    def enterTest(self, ctx:Python3Parser.TestContext):
        pass

    # Exit a parse tree produced by Python3Parser#test.
    def exitTest(self, ctx:Python3Parser.TestContext):
        pass


    # Enter a parse tree produced by Python3Parser#test_nocond.
    def enterTest_nocond(self, ctx:Python3Parser.Test_nocondContext):
        pass

    # Exit a parse tree produced by Python3Parser#test_nocond.
    def exitTest_nocond(self, ctx:Python3Parser.Test_nocondContext):
        pass


    # Enter a parse tree produced by Python3Parser#lambdef.
    def enterLambdef(self, ctx:Python3Parser.LambdefContext):
        pass

    # Exit a parse tree produced by Python3Parser#lambdef.
    def exitLambdef(self, ctx:Python3Parser.LambdefContext):
        pass


    # Enter a parse tree produced by Python3Parser#lambdef_nocond.
    def enterLambdef_nocond(self, ctx:Python3Parser.Lambdef_nocondContext):
        pass

    # Exit a parse tree produced by Python3Parser#lambdef_nocond.
    def exitLambdef_nocond(self, ctx:Python3Parser.Lambdef_nocondContext):
        pass


    # Enter a parse tree produced by Python3Parser#or_test.
    def enterOr_test(self, ctx:Python3Parser.Or_testContext):
        pass

    # Exit a parse tree produced by Python3Parser#or_test.
    def exitOr_test(self, ctx:Python3Parser.Or_testContext):
        pass


    # Enter a parse tree produced by Python3Parser#and_test.
    def enterAnd_test(self, ctx:Python3Parser.And_testContext):
        pass

    # Exit a parse tree produced by Python3Parser#and_test.
    def exitAnd_test(self, ctx:Python3Parser.And_testContext):
        pass


    # Enter a parse tree produced by Python3Parser#not_test.
    def enterNot_test(self, ctx:Python3Parser.Not_testContext):
        pass

    # Exit a parse tree produced by Python3Parser#not_test.
    def exitNot_test(self, ctx:Python3Parser.Not_testContext):
        pass


    # Enter a parse tree produced by Python3Parser#comparison.
    def enterComparison(self, ctx:Python3Parser.ComparisonContext):
        pass

    # Exit a parse tree produced by Python3Parser#comparison.
    def exitComparison(self, ctx:Python3Parser.ComparisonContext):
        pass


    # Enter a parse tree produced by Python3Parser#comp_op.
    def enterComp_op(self, ctx:Python3Parser.Comp_opContext):
        pass

    # Exit a parse tree produced by Python3Parser#comp_op.
    def exitComp_op(self, ctx:Python3Parser.Comp_opContext):
        pass


    # Enter a parse tree produced by Python3Parser#star_expr.
    def enterStar_expr(self, ctx:Python3Parser.Star_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#star_expr.
    def exitStar_expr(self, ctx:Python3Parser.Star_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#expr.
    def enterExpr(self, ctx:Python3Parser.ExprContext):
        pass

    # Exit a parse tree produced by Python3Parser#expr.
    def exitExpr(self, ctx:Python3Parser.ExprContext):
        pass


    # Enter a parse tree produced by Python3Parser#xor_expr.
    def enterXor_expr(self, ctx:Python3Parser.Xor_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#xor_expr.
    def exitXor_expr(self, ctx:Python3Parser.Xor_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#and_expr.
    def enterAnd_expr(self, ctx:Python3Parser.And_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#and_expr.
    def exitAnd_expr(self, ctx:Python3Parser.And_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#shift_expr.
    def enterShift_expr(self, ctx:Python3Parser.Shift_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#shift_expr.
    def exitShift_expr(self, ctx:Python3Parser.Shift_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#arith_expr.
    def enterArith_expr(self, ctx:Python3Parser.Arith_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#arith_expr.
    def exitArith_expr(self, ctx:Python3Parser.Arith_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#term.
    def enterTerm(self, ctx:Python3Parser.TermContext):
        pass

    # Exit a parse tree produced by Python3Parser#term.
    def exitTerm(self, ctx:Python3Parser.TermContext):
        pass


    # Enter a parse tree produced by Python3Parser#factor.
    def enterFactor(self, ctx:Python3Parser.FactorContext):
        pass

    # Exit a parse tree produced by Python3Parser#factor.
    def exitFactor(self, ctx:Python3Parser.FactorContext):
        pass


    # Enter a parse tree produced by Python3Parser#power.
    def enterPower(self, ctx:Python3Parser.PowerContext):
        pass

    # Exit a parse tree produced by Python3Parser#power.
    def exitPower(self, ctx:Python3Parser.PowerContext):
        pass


    # Enter a parse tree produced by Python3Parser#atom.
    def enterAtom(self, ctx:Python3Parser.AtomContext):
        pass

    # Exit a parse tree produced by Python3Parser#atom.
    def exitAtom(self, ctx:Python3Parser.AtomContext):
        pass


    # Enter a parse tree produced by Python3Parser#testlist_comp.
    def enterTestlist_comp(self, ctx:Python3Parser.Testlist_compContext):
        pass

    # Exit a parse tree produced by Python3Parser#testlist_comp.
    def exitTestlist_comp(self, ctx:Python3Parser.Testlist_compContext):
        pass


    # Enter a parse tree produced by Python3Parser#trailer.
    def enterTrailer(self, ctx:Python3Parser.TrailerContext):
        pass

    # Exit a parse tree produced by Python3Parser#trailer.
    def exitTrailer(self, ctx:Python3Parser.TrailerContext):
        pass


    # Enter a parse tree produced by Python3Parser#subscriptlist.
    def enterSubscriptlist(self, ctx:Python3Parser.SubscriptlistContext):
        pass

    # Exit a parse tree produced by Python3Parser#subscriptlist.
    def exitSubscriptlist(self, ctx:Python3Parser.SubscriptlistContext):
        pass


    # Enter a parse tree produced by Python3Parser#subscript.
    def enterSubscript(self, ctx:Python3Parser.SubscriptContext):
        pass

    # Exit a parse tree produced by Python3Parser#subscript.
    def exitSubscript(self, ctx:Python3Parser.SubscriptContext):
        pass


    # Enter a parse tree produced by Python3Parser#sliceop.
    def enterSliceop(self, ctx:Python3Parser.SliceopContext):
        pass

    # Exit a parse tree produced by Python3Parser#sliceop.
    def exitSliceop(self, ctx:Python3Parser.SliceopContext):
        pass


    # Enter a parse tree produced by Python3Parser#exprlist.
    def enterExprlist(self, ctx:Python3Parser.ExprlistContext):
        pass

    # Exit a parse tree produced by Python3Parser#exprlist.
    def exitExprlist(self, ctx:Python3Parser.ExprlistContext):
        pass


    # Enter a parse tree produced by Python3Parser#testlist.
    def enterTestlist(self, ctx:Python3Parser.TestlistContext):
        pass

    # Exit a parse tree produced by Python3Parser#testlist.
    def exitTestlist(self, ctx:Python3Parser.TestlistContext):
        pass


    # Enter a parse tree produced by Python3Parser#dictorsetmaker.
    def enterDictorsetmaker(self, ctx:Python3Parser.DictorsetmakerContext):
        pass

    # Exit a parse tree produced by Python3Parser#dictorsetmaker.
    def exitDictorsetmaker(self, ctx:Python3Parser.DictorsetmakerContext):
        pass


    # Enter a parse tree produced by Python3Parser#classdef.
    def enterClassdef(self, ctx:Python3Parser.ClassdefContext):
        pass

    # Exit a parse tree produced by Python3Parser#classdef.
    def exitClassdef(self, ctx:Python3Parser.ClassdefContext):
        pass


    # Enter a parse tree produced by Python3Parser#arglist.
    def enterArglist(self, ctx:Python3Parser.ArglistContext):
        pass

    # Exit a parse tree produced by Python3Parser#arglist.
    def exitArglist(self, ctx:Python3Parser.ArglistContext):
        pass


    # Enter a parse tree produced by Python3Parser#argument.
    def enterArgument(self, ctx:Python3Parser.ArgumentContext):
        pass

    # Exit a parse tree produced by Python3Parser#argument.
    def exitArgument(self, ctx:Python3Parser.ArgumentContext):
        pass


    # Enter a parse tree produced by Python3Parser#comp_iter.
    def enterComp_iter(self, ctx:Python3Parser.Comp_iterContext):
        pass

    # Exit a parse tree produced by Python3Parser#comp_iter.
    def exitComp_iter(self, ctx:Python3Parser.Comp_iterContext):
        pass


    # Enter a parse tree produced by Python3Parser#comp_for.
    def enterComp_for(self, ctx:Python3Parser.Comp_forContext):
        pass

    # Exit a parse tree produced by Python3Parser#comp_for.
    def exitComp_for(self, ctx:Python3Parser.Comp_forContext):
        pass


    # Enter a parse tree produced by Python3Parser#comp_if.
    def enterComp_if(self, ctx:Python3Parser.Comp_ifContext):
        pass

    # Exit a parse tree produced by Python3Parser#comp_if.
    def exitComp_if(self, ctx:Python3Parser.Comp_ifContext):
        pass


    # Enter a parse tree produced by Python3Parser#yield_expr.
    def enterYield_expr(self, ctx:Python3Parser.Yield_exprContext):
        pass

    # Exit a parse tree produced by Python3Parser#yield_expr.
    def exitYield_expr(self, ctx:Python3Parser.Yield_exprContext):
        pass


    # Enter a parse tree produced by Python3Parser#yield_arg.
    def enterYield_arg(self, ctx:Python3Parser.Yield_argContext):
        pass

    # Exit a parse tree produced by Python3Parser#yield_arg.
    def exitYield_arg(self, ctx:Python3Parser.Yield_argContext):
        pass


    # Enter a parse tree produced by Python3Parser#strr.
    def enterStrr(self, ctx:Python3Parser.StrrContext):
        pass

    # Exit a parse tree produced by Python3Parser#strr.
    def exitStrr(self, ctx:Python3Parser.StrrContext):
        pass


    # Enter a parse tree produced by Python3Parser#number.
    def enterNumber(self, ctx:Python3Parser.NumberContext):
        pass

    # Exit a parse tree produced by Python3Parser#number.
    def exitNumber(self, ctx:Python3Parser.NumberContext):
        pass


    # Enter a parse tree produced by Python3Parser#integer.
    def enterInteger(self, ctx:Python3Parser.IntegerContext):
        pass

    # Exit a parse tree produced by Python3Parser#integer.
    def exitInteger(self, ctx:Python3Parser.IntegerContext):
        pass


