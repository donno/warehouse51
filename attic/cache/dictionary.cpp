// Created April 2012
#include <iostream>
#include <string>
#include <vector>

using namespace std;
 
class Expression {
 
        char *word_with_several_meanings; // like "bank", "class"
        vector<string> meanings; // Stores all the meanings
 
        //-----------FUNCTIONS------------------------------------------------
public:
        void word( const char*);
        void add_meaning(const char*);
        char* get_word();
        int get_total_number_of_meanings() const;
        const std::string& get_meaning(int meanx = 0) const;
        Expression(int mctr = 0); // CTOR
        ~Expression(); // DTOR
};
 
Expression::Expression(int mctr ) {
  meanings.reserve(10); // Reserve space for 10 meanings but more space will be allocated if needed.
}
 
Expression::~Expression() {
  delete [] word_with_several_meanings; // Deleting the memory we allocated
}
 
void Expression::word( const char *p2c )
{
 
        word_with_several_meanings = new char[strlen(p2c)+1];
// copy the string, DEEP copy
        strcpy(word_with_several_meanings, p2c);
}
 
void Expression::add_meaning(const char *p2c)
{
        meanings.push_back(p2c);        
}
 
const string& Expression::get_meaning( int meanx ) const
{
        return meanings[meanx];
}
 
char * Expression::get_word()
{
  return word_with_several_meanings;
}
 
int Expression::get_total_number_of_meanings() const
{
  return meanings.size();
}
 
int main(void) {
        int i;
        Expression expr;
        expr.word("bank");
        expr.add_meaning("a place to get money from");
        expr.add_meaning("b place to sit");
        expr.add_meaning("4 letter word");
        expr.add_meaning("Test meaning");
        cout << expr.get_word() << endl;
 
        for(int i = 0; i<expr.get_total_number_of_meanings(); i++)
                cout << " " << expr.get_meaning(i)  << endl;
        Expression expr2;
        expr2.word("class");
        expr2.add_meaning("a school class");
        expr2.add_meaning("a classification for a hotel");
        expr2.add_meaning("Starts with C");
        cout << expr2.get_word() << endl;
        for( i = 0; i<expr2.get_total_number_of_meanings(); i++)
                cout << " " << expr2.get_meaning(i) << endl;
 
        Expression expr3;
        expr3.word("A very long test");
        char str[] = "Meaning_    ";
        for(int kx =0; kx<26; kx++){
                str[8] = ('A'+kx);
                expr3.add_meaning(str);
        }
 
        cout << expr3.get_word() << endl;
        for( int i = 0; i<expr3.get_total_number_of_meanings(); i++)
                cout << " " << expr3.get_meaning(i) << endl;
        return 0;
}