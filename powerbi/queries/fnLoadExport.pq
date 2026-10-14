// Shared loader for the CSVs written by `python -m tracker refresh`.
// Empty cells become null before typing, otherwise number columns error out.
(name as text, types as list) as table =>
let
    Source   = Csv.Document(
                   File.Contents(ExportFolder & "\" & name & ".csv"),
                   [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Nulls    = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed    = Table.TransformColumnTypes(Nulls, types, "en-US")
in
    Typed
